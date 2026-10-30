import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from addgame import open_add_game
from updategame import open_update_game
from database import (
    backup_database as create_database_backup, connect_database,
    get_recycled_games, move_game_to_recycle_bin, restore_game
)


def filter_games(games, keyword="", platform="", genre="", year=""):
    keyword = keyword.strip().casefold()

    return [
        game for game in games
        if (not keyword or any(
            keyword in str(value).casefold()
            for value in game[1:4]
            if value is not None
        ))
        and (not platform or str(game[2]) == platform)
        and (not genre or str(game[3]) == genre)
        and (not year or str(game[4]) == year)
    ]


def open_dashboard(login_root, read_only=False):
    login_root.withdraw()

    dashboard = tk.Toplevel()
    dashboard.title("GameVault - View Games" if read_only else "GameVault - Dashboard")
    dashboard.geometry("1040x680")
    dashboard.resizable(False, False)

    navy = "#101B2D"
    orange = "#F26B4F"
    white = "#FFFFFF"
    soft = "#F4F7FA"
    text = "#17202E"

    games = []

    def load_games():
        nonlocal games

        try:
            conn = connect_database()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT game_id, title, platform, genre, release_year
                FROM games
                WHERE deleted_at IS NULL
                ORDER BY game_id ASC
            """)

            games = cursor.fetchall()

            cursor.close()
            conn.close()

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=dashboard
            )
            return

        for box, variable, column in filter_controls:
            options = sorted(
                {
                    str(game[column])
                    for game in games
                    if game[column] is not None
                },
                reverse=column == 4
            )

            box["values"] = ["All"] + options

            if variable.get() not in box["values"]:
                variable.set("All")

        search_games()

    def search_games(event=None):
        matches = filter_games(
            games,
            search_entry.get(),
            *(
                "" if variable.get() == "All"
                else variable.get()
                for _, variable, _ in filter_controls
            )
        )

        game_table.delete(*game_table.get_children())

        for game in matches:
            game_table.insert(
                "",
                tk.END,
                values=game
            )

        result_text.set(
            f"Showing {len(matches)} of {len(games)} games"
        )

    def clear_filters():
        search_entry.delete(0, tk.END)

        for _, variable, _ in filter_controls:
            variable.set("All")

        search_games()

    def on_game_saved(game_id):
        load_games()
        clear_filters()
        for item in game_table.get_children():
            if str(game_table.item(item)["values"][0]) == str(game_id):
                game_table.selection_set(item)
                game_table.see(item)
                break

    def add_game():
        if read_only:
            return
        open_add_game(dashboard, on_game_saved)

    def update_game():
        if read_only:
            return
        selected = game_table.selection()

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Please select a game."
            )
            return

        game = game_table.item(
            selected[0]
        )["values"]

        open_update_game(dashboard, game[0], on_game_saved)

    def delete_game():
        if read_only:
            return
        selected = game_table.selection()

        if not selected:
            messagebox.showwarning(
                "Warning",
                "Please select a game."
            )
            return

        game = game_table.item(
            selected[0]
        )["values"]

        confirm = messagebox.askyesno(
            "Move to Recycle Bin",
            f"Move {game[1]} to the Recycle Bin? You can restore it later.",
            parent=dashboard
        )

        if confirm:
            try:
                move_game_to_recycle_bin(game[0])
                load_games()

            except Exception as error:
                messagebox.showerror(
                    "Database Error",
                    str(error)
                )

    def open_recycle_bin():
        if read_only:
            return
        window = tk.Toplevel(dashboard)
        window.title("GameVault - Recycle Bin")
        window.geometry("850x450")
        window.transient(dashboard)
        window.grab_set()

        tk.Label(
            window, text="Recycle Bin", font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(
            window, text="Select a game and click Restore to return it to your list."
        ).pack(anchor="w", padx=20, pady=(0, 10))

        frame = ttk.Frame(window)
        frame.pack(fill="both", expand=True, padx=20)
        table = ttk.Treeview(
            frame, columns=columns, show="headings", selectmode="browse"
        )
        for column, width in zip(columns, (60, 280, 150, 170, 100)):
            table.heading(column, text=column)
            table.column(column, width=width, minwidth=40)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        table.pack(side="left", fill="both", expand=True)

        status = tk.StringVar()
        tk.Label(window, textvariable=status).pack(anchor="w", padx=20, pady=8)

        def refresh_bin():
            try:
                recycled = get_recycled_games()
            except Exception as error:
                messagebox.showerror("Database Error", str(error), parent=window)
                return
            table.delete(*table.get_children())
            for game in recycled:
                table.insert("", tk.END, iid=str(game[0]), values=game)
            status.set(
                f"{len(recycled)} game(s) in Recycle Bin"
                if recycled else "Recycle Bin is empty."
            )

        def restore_selected():
            selected = table.selection()
            if not selected:
                messagebox.showwarning(
                    "Select a Game", "Please select a game to restore.", parent=window
                )
                return
            try:
                restore_game(int(selected[0]))
            except Exception as error:
                messagebox.showerror("Database Error", str(error), parent=window)
                return
            load_games()
            clear_filters()
            refresh_bin()

        actions = ttk.Frame(window)
        actions.pack(fill="x", padx=20, pady=(0, 20))
        ttk.Button(actions, text="Restore", command=restore_selected).pack(side="left")
        ttk.Button(actions, text="Close", command=window.destroy).pack(side="right")
        refresh_bin()

    def logout():
        if read_only:
            dashboard.destroy()
            login_root.deiconify()
            return

        if messagebox.askyesno(
            "Logout",
            "Logout now?"
        ):
            dashboard.destroy()
            login_root.deiconify()

    def backup_collection():
        destination = filedialog.asksaveasfilename(
            parent=dashboard,
            title="Back Up GameVault Database",
            initialfile="gamevault-backup.db",
            defaultextension=".db",
            filetypes=(("SQLite database", "*.db"), ("All files", "*.*"))
        )
        if not destination:
            return
        try:
            create_database_backup(destination)
        except Exception as error:
            messagebox.showerror("Backup Failed", str(error), parent=dashboard)
            return
        messagebox.showinfo(
            "Backup Complete", "Your GameVault database was backed up.", parent=dashboard
        )

    # HEADER
    header = tk.Frame(
        dashboard,
        bg=navy,
        height=75
    )

    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        header,
        text="GAMEVAULT",
        font=("Segoe UI", 22, "bold"),
        bg=navy,
        fg=white
    ).pack(
        side="left",
        padx=40
    )

    tk.Label(
        header,
        text="VIEW ONLY" if read_only else "ADMIN DASHBOARD",
        font=("Segoe UI", 10, "bold"),
        bg=navy,
        fg="#91A1B5"
    ).pack(
        side="right",
        padx=40
    )

    # CARD
    card = tk.Frame(
        dashboard,
        bg=white
    )

    card.pack(
        fill="both",
        expand=True,
        padx=45,
        pady=25
    )

    # TITLE
    top = tk.Frame(
        card,
        bg=white
    )

    top.pack(
        fill="x",
        padx=30,
        pady=(25, 15)
    )

    tk.Label(
        top,
        text="Dashboard",
        font=("Segoe UI", 24, "bold"),
        bg=white,
        fg=text
    ).pack(
        side="left"
    )

    if not read_only:
        tk.Button(
            top,
            text="+ ADD GAME",
            bg=orange,
            fg=white,
            relief="flat",
            command=add_game
        ).pack(
            side="right",
            ipadx=12,
            ipady=6
        )

    # SEARCH
    tk.Label(
        card,
        text="Search by title, platform, or genre",
        bg=white,
        fg=text,
        font=("Segoe UI", 10)
    ).pack(
        anchor="w",
        padx=30,
        pady=(0, 5)
    )

    search_entry = tk.Entry(
        card,
        font=("Segoe UI", 11),
        bg=soft,
        relief="flat"
    )

    search_entry.pack(
        fill="x",
        padx=30,
        ipady=8,
        pady=(0, 15)
    )

    search_entry.bind(
        "<KeyRelease>",
        search_games
    )

    # FILTERS
    filters = tk.Frame(
        card,
        bg=white
    )

    filters.pack(
        fill="x",
        padx=30,
        pady=(0, 10)
    )

    filter_controls = []

    for label, column in (
        ("Platform", 2),
        ("Genre", 3),
        ("Release year", 4)
    ):
        group = tk.Frame(
            filters,
            bg=white
        )

        group.pack(
            side="left",
            padx=(0, 16)
        )

        tk.Label(
            group,
            text=label,
            bg=white,
            fg=text
        ).pack(
            anchor="w"
        )

        variable = tk.StringVar(
            value="All"
        )

        box = ttk.Combobox(
            group,
            textvariable=variable,
            values=["All"],
            state="readonly",
            width=19
        )

        box.pack(
            pady=(4, 0)
        )

        box.bind(
            "<<ComboboxSelected>>",
            search_games
        )

        filter_controls.append(
            (box, variable, column)
        )

    tk.Button(
        filters,
        text="Clear Filters",
        command=clear_filters
    ).pack(
        side="right"
    )

    result_text = tk.StringVar(
        value="Loading games..."
    )

    tk.Label(
        card,
        textvariable=result_text,
        bg=white,
        fg=text
    ).pack(
        anchor="w",
        padx=30,
        pady=(0, 8)
    )

    # TABLE
    columns = (
        "ID",
        "Title",
        "Platform",
        "Genre",
        "Year"
    )

    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview.Heading",
        background="black",
        foreground="white",
        font=("Segoe UI", 10, "bold")
    )

    game_table = ttk.Treeview(
        card,
        columns=columns,
        show="headings"
    )

    for column in columns:
        game_table.heading(
            column,
            text=column
        )

    game_table.column(
        "ID",
        width=60,
        anchor="center"
    )

    game_table.column(
        "Title",
        width=280
    )

    game_table.column(
        "Platform",
        width=150,
        anchor="center"
    )

    game_table.column(
        "Genre",
        width=170,
        anchor="center"
    )

    game_table.column(
        "Year",
        width=100,
        anchor="center"
    )

    game_table.pack(
        fill="both",
        expand=True,
        padx=30
    )

    # BUTTONS
    buttons = tk.Frame(
        card,
        bg=white
    )

    buttons.pack(
        fill="x",
        padx=30,
        pady=20
    )

    if not read_only:
        tk.Button(
            buttons,
            text="Update",
            width=12,
            command=update_game
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="Delete",
            width=12,
            bg=orange,
            fg=white,
            command=delete_game
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="Recycle Bin",
            width=12,
            command=open_recycle_bin
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="Back Up",
            width=12,
            command=backup_collection
        ).pack(side="left", padx=5)

    tk.Button(
        buttons,
        text="Refresh",
        width=12,
        command=load_games
    ).pack(
        side="left",
        padx=5
    )

    tk.Button(
        buttons,
        text="Back" if read_only else "Logout",
        width=12,
        bg=navy,
        fg=white,
        command=logout
    ).pack(
        side="right"
    )

    load_games()

    dashboard.protocol(
        "WM_DELETE_WINDOW",
        login_root.destroy
    )
