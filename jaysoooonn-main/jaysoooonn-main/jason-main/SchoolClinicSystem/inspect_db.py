
import sqlite3
from database import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)

tables = conn.execute("""
    SELECT name, sql
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
""")

for name, sql in tables:
    print(f"\nTABLE: {name}\n{sql}")

conn.close()
