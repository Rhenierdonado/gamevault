import tkinter as tk
from tkinter import messagebox

from database import get_admin
from dashboard import open_dashboard


def start_login():
    root = tk.Tk()
    root.title("GameVault - Admin Login")
    root.geometry("1040x680")
    root.resizable(False, False)

    navy = "#101B2D"
    orange = "#F26B4F"
    white = "#FFFFFF"
    soft = "#F4F7FA"
    text = "#17202E"
    muted = "#687588"

    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Please enter username and password."
            )
            return

        try:
            admin = get_admin(username, password)

            if admin:
                messagebox.showinfo(
                    "Login Successful",
                    "Welcome to GameVault!"
                )

                open_dashboard(root)

            else:
                messagebox.showerror(
                    "Login Failed",
                    "Incorrect username or password."
                )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error)
            )

    # MAIN FRAME
    main_frame = tk.Frame(root, bg=navy)
    main_frame.pack(fill="both", expand=True)

    # LEFT SIDE
    brand_frame = tk.Frame(
        main_frame,
        bg=navy,
        width=430
    )
    brand_frame.pack(side="left", fill="y")
    brand_frame.pack_propagate(False)

    tk.Label(
        brand_frame,
        text="GV",
        font=("Segoe UI", 18, "bold"),
        bg=orange,
        fg=white,
        width=4,
        height=2
    ).pack(
        anchor="w",
        padx=52,
        pady=(58, 35)
    )

    tk.Label(
        brand_frame,
        text="GAMEVAULT",
        font=("Segoe UI", 30, "bold"),
        bg=navy,
        fg=white
    ).pack(
        anchor="w",
        padx=52
    )

    tk.Label(
        brand_frame,
        text="VIDEO GAME COLLECTION\nMANAGEMENT SYSTEM",
        font=("Segoe UI", 17, "bold"),
        bg=navy,
        fg="#D8E0EA",
        justify="left"
    ).pack(
        anchor="w",
        padx=52,
        pady=(8, 20)
    )

    tk.Frame(
        brand_frame,
        bg=orange,
        width=300,
        height=4
    ).pack(
        anchor="w",
        padx=52,
        pady=(0, 25)
    )

    tk.Label(
        brand_frame,
        text="Manage your games, find your favorite genre\nand enjoy your game.",
        font=("Segoe UI", 11),
        bg=navy,
        fg="#91A1B5",
        justify="left"
    ).pack(
        anchor="w",
        padx=52
    )

    tk.Label(
        brand_frame,
        text="ADMIN CONSOLE / 2026",
        font=("Segoe UI", 9, "bold"),
        bg=navy,
        fg="#60738B"
    ).pack(
        anchor="w",
        padx=52,
        pady=(225, 0)
    )

    # RIGHT SIDE
    content_frame = tk.Frame(
        main_frame,
        bg=soft
    )
    content_frame.pack(
        side="right",
        fill="both",
        expand=True
    )

    login_card = tk.Frame(
        content_frame,
        bg=white,
        width=430,
        height=490
    )
    login_card.place(
        relx=0.5,
        rely=0.5,
        anchor="center"
    )
    login_card.pack_propagate(False)

    tk.Label(
        login_card,
        text="Welcome",
        font=("Segoe UI", 25, "bold"),
        bg=white,
        fg=text
    ).pack(
        anchor="w",
        padx=52,
        pady=(48, 5)
    )

    login_subtitle = tk.Label(
        login_card,
        text="Sign in to access your GameVault dashboard.",
        font=("Segoe UI", 10),
        bg=white,
        fg=muted
    )
    login_subtitle.pack(
        anchor="w",
        padx=52,
        pady=(0, 34)
    )

    tk.Label(
        login_card,
        text="USERNAME",
        font=("Segoe UI", 9, "bold"),
        bg=white,
        fg=muted
    ).pack(
        anchor="w",
        padx=52
    )

    username_entry = tk.Entry(
        login_card,
        font=("Segoe UI", 12),
        bg=soft,
        relief="flat"
    )
    username_entry.pack(
        fill="x",
        padx=52,
        ipady=11,
        pady=(7, 23)
    )

    tk.Label(
        login_card,
        text="PASSWORD",
        font=("Segoe UI", 9, "bold"),
        bg=white,
        fg=muted
    ).pack(
        anchor="w",
        padx=52
    )

    password_row = tk.Frame(login_card, bg=soft)
    password_row.pack(
        fill="x",
        padx=52,
        pady=(7, 30)
    )

    password_entry = tk.Entry(
        password_row,
        font=("Segoe UI", 12),
        bg=soft,
        show="*",
        relief="flat",
        bd=0
    )
    password_entry.pack(side="left", fill="x", expand=True, ipady=11)

    def toggle_password_visibility():
        is_hidden = password_entry.cget("show") == "*"
        password_entry.config(show="" if is_hidden else "*")
        visibility_button.config(text="Hide" if is_hidden else "Show")

    visibility_button = tk.Button(
        password_row,
        text="Show",
        font=("Segoe UI", 9),
        bg=soft,
        fg=muted,
        activebackground=soft,
        relief="flat",
        bd=0,
        cursor="hand2",
        command=toggle_password_visibility
    )
    visibility_button.pack(side="right", padx=(8, 10))

    tk.Button(
        login_card,
        text="SIGN IN",
        font=("Segoe UI", 11, "bold"),
        bg=orange,
        fg=white,
        relief="flat",
        cursor="hand2",
        command=login
    ).pack(
        fill="x",
        padx=52,
        ipady=11
    )

    tk.Button(
        login_card,
        text="VIEW GAMES", 
        font=("Segoe UI", 10, "bold"),
        bg=soft,
        fg=text,
        relief="flat",
        cursor="hand2",
        command=lambda: open_dashboard(root, read_only=True)
    ).pack(
        fill="x",
        padx=52,
        ipady=8,
        pady=(10, 0)
    )

    tk.Label(
        login_card,
        text="Authorized personnel only",
        font=("Segoe UI", 9),
        bg=white,
        fg="#9AA5B2"
    ).pack(
        pady=(28, 0)
    )

    root.bind(
        "<Return>",
        lambda event: login()
    )

    username_entry.focus_set()
    root.mainloop()
