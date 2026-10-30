import hashlib
import hmac
import os
import sqlite3
import secrets
from contextlib import closing


SUPPORTED_PLATFORMS = (
    "PC", "PlayStation 5", "PlayStation 4", "Xbox Series X/S", "Xbox One",
    "Xbox 360", "Nintendo Switch", "Android", "iOS", "Other"
)
SUPPORTED_GENRES = (
    "Action", "Adventure", "RPG", "Strategy", "Simulation", "Sports",
    "Racing", "Puzzle", "Horror", "Fighting", "Other"
)


def connect_database():
    return sqlite3.connect("gamevault.db")


def backup_database(destination):
    if os.path.abspath(destination) == os.path.abspath("gamevault.db"):
        raise ValueError("Choose a different file from the active database.")
    with closing(connect_database()) as source, closing(sqlite3.connect(destination)) as target:
        source.backup(target)


def _hash_password(password):
    salt = secrets.token_bytes(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_password(stored_password, password):
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, digest_hex = stored_password.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(
        stored_password.encode("utf-8"), password.encode("utf-8")
    )


def create_tables():
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    admin_columns = {row[1] for row in cursor.execute("PRAGMA table_info(admin)")}
    if "role" in admin_columns:
        cursor.execute("ALTER TABLE admin RENAME TO admin_with_role")
        cursor.execute("""
            CREATE TABLE admin (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            INSERT INTO admin (admin_id, username, password)
            SELECT admin_id, username, password FROM admin_with_role
        """)
        cursor.execute("DROP TABLE admin_with_role")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            platform TEXT NOT NULL,
            genre TEXT NOT NULL,
            release_year INTEGER
        )
    """)

    # Upgrade existing databases without changing their game records.
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(games)")}
    if "deleted_at" not in columns:
        cursor.execute("ALTER TABLE games ADD COLUMN deleted_at TEXT")

    # Keep existing records aligned with the options offered by the game form.
    cursor.execute("UPDATE games SET platform = 'Other' WHERE platform NOT IN ({})".format(
        ",".join("?" for _ in SUPPORTED_PLATFORMS)
    ), SUPPORTED_PLATFORMS)
    cursor.execute("""
        UPDATE games
        SET genre = CASE
            WHEN LOWER(genre) IN ('shooter', 'arcade') THEN 'Action'
            WHEN LOWER(genre) = 'platformer' THEN 'Adventure'
            WHEN LOWER(genre) = 'card' THEN 'Strategy'
            ELSE 'Other'
        END
        WHERE genre NOT IN ({})
    """.format(",".join("?" for _ in SUPPORTED_GENRES)), SUPPORTED_GENRES)

    if cursor.execute("SELECT 1 FROM admin LIMIT 1").fetchone() is None:
        cursor.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", _hash_password("admin123"))
        )

    conn.commit()
    conn.close()


def get_admin(username, password):
    with closing(connect_database()) as conn, conn:
        row = conn.execute(
            "SELECT admin_id, username, password FROM admin WHERE username = ?",
            (username,)
        ).fetchone()
        if row is None or not _verify_password(row[2], password):
            return None
        if not row[2].startswith("pbkdf2_sha256$"):
            conn.execute(
                "UPDATE admin SET password = ? WHERE admin_id = ?",
                (_hash_password(password), row[0])
            )
        return row[0], row[1]


def validate_game_details(title, platform, genre, release_year=""):
    title, platform, genre = (value.strip() for value in (title, platform, genre))
    if not all((title, platform, genre)):
        raise ValueError("Title, platform, and genre are required.")
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError("Choose a platform from the available options.")
    if genre not in SUPPORTED_GENRES:
        raise ValueError("Choose a genre from the available options.")
    year_text = str(release_year).strip() if release_year is not None else ""
    year = None
    if year_text:
        if not year_text.isascii() or not year_text.isdigit() or len(year_text) != 4:
            raise ValueError("Release year must be a four-digit year, or left blank.")
        year = int(year_text)
        if year < 1000:
            raise ValueError("Release year must be between 1000 and 9999.")
    return title, platform, genre, year


def insert_game(title, platform, genre, release_year=""):
    details = validate_game_details(title, platform, genre, release_year)
    with closing(connect_database()) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO games (title, platform, genre, release_year) VALUES (?, ?, ?, ?)",
            details
        )
        return cursor.lastrowid


def get_game(game_id):
    with closing(connect_database()) as conn:
        return conn.execute(
            "SELECT game_id, title, platform, genre, release_year FROM games "
            "WHERE game_id = ? AND deleted_at IS NULL", (game_id,)
        ).fetchone()


def update_game_details(game_id, title, platform, genre, release_year=""):
    details = validate_game_details(title, platform, genre, release_year)
    with closing(connect_database()) as conn, conn:
        cursor = conn.execute(
            "UPDATE games SET title = ?, platform = ?, genre = ?, release_year = ? "
            "WHERE game_id = ? AND deleted_at IS NULL", (*details, game_id)
        )
        if cursor.rowcount != 1:
            raise sqlite3.DatabaseError("This game is no longer available for editing. Refresh the list.")
    return game_id


def move_game_to_recycle_bin(game_id):
    with closing(connect_database()) as conn, conn:
        conn.execute(
            "UPDATE games SET deleted_at = CURRENT_TIMESTAMP "
            "WHERE game_id = ? AND deleted_at IS NULL",
            (game_id,)
        )


def restore_game(game_id):
    with closing(connect_database()) as conn, conn:
        conn.execute(
            "UPDATE games SET deleted_at = NULL WHERE game_id = ?",
            (game_id,)
        )


def get_recycled_games():
    with closing(connect_database()) as conn:
        return conn.execute(
            "SELECT game_id, title, platform, genre, release_year FROM games "
            "WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC, game_id DESC"
        ).fetchall()
