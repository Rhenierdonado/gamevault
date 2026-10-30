import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from database import insert_game, SUPPORTED_GENRES, SUPPORTED_PLATFORMS


def open_add_game(parent, on_saved):
    return open_game_form(parent, on_saved, insert_game)


def open_game_form(parent, on_saved, save_details, game=None):
    editing = game is not None
    form_title = "Update Game" if editing else "Add Game"
    window = tk.Toplevel(parent)
    window.title(f"GameVault - {form_title}")
    window.geometry("620x650")
    window.resizable(False, False)
    window.configure(bg="#F4F7FA")
    window.transient(parent)
    window.grab_set()

    navy = "#101B2D"
    orange = "#F26B4F"
    text = "#17202E"

    header = tk.Frame(window, bg=navy)
    header.pack(fill="x")
    tk.Label(
        header, text="GAMEVAULT", font=("Segoe UI", 20, "bold"),
        bg=navy, fg="white"
    ).pack(side="left", padx=30, pady=20)
    tk.Label(
        header, text="YOUR COLLECTION", font=("Segoe UI", 9, "bold"),
        bg=navy, fg="#91A1B5"
    ).pack(side="right", padx=30)

    card = tk.Frame(window, bg="white")
    card.pack(fill="both", expand=True, padx=30, pady=25)
    tk.Label(
        card, text=form_title, font=("Segoe UI", 24, "bold"),
        bg="white", fg=text
    ).pack(anchor="w", padx=28, pady=(22, 4))
    tk.Label(
        card, text=("Edit your game's details. * Required fields" if editing
                    else "Add a new title to your collection. * Required fields"),
        font=("Segoe UI", 10), bg="white", fg="#687588"
    ).pack(anchor="w", padx=28, pady=(0, 18))

    fields = {}
    suggestions = {
        "platform": SUPPORTED_PLATFORMS,
        "genre": SUPPORTED_GENRES
    }
    for key, label in (
        ("title", "GAME TITLE *"), ("platform", "PLATFORM *"),
        ("genre", "GENRE *"), ("year", "RELEASE YEAR (OPTIONAL)")
    ):
        tk.Label(
            card, text=label, font=("Segoe UI", 9, "bold"),
            bg="white", fg="#687588"
        ).pack(anchor="w", padx=28)
        if key in suggestions:
            entry = ttk.Combobox(
                card, values=suggestions[key], font=("Segoe UI", 11),
                state="readonly"
            )
        else:
            entry = tk.Entry(
                card, font=("Segoe UI", 11), bg="#F4F7FA", relief="flat"
            )
        entry.pack(fill="x", padx=28, pady=(5, 15), ipady=6)
        fields[key] = entry

    if editing:
        for key, value in zip(("title", "platform", "genre", "year"), game[1:]):
            fields[key].insert(0, "" if value is None else str(value))

    def save_game(event=None):
        for key in ("title", "platform", "genre"):
            if not fields[key].get().strip():
                messagebox.showwarning(
                    "Missing Information", f"Please enter a game {key}.", parent=window
                )
                fields[key].focus_set()
                return
        try:
            game_id = save_details(
                fields["title"].get(), fields["platform"].get(),
                fields["genre"].get(), fields["year"].get()
            )
        except ValueError as error:
            messagebox.showwarning("Invalid Information", str(error), parent=window)
            fields["year"].focus_set()
            return
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not save the game.\n{error}", parent=window
            )
            return
        window.destroy()
        on_saved(game_id)
        messagebox.showinfo(
            "Game Updated" if editing else "Game Added",
            "Your changes were saved." if editing else "Your game was added to the collection.",
            parent=parent
        )

    actions = tk.Frame(card, bg="white")
    actions.pack(fill="x", padx=28, pady=(5, 20))
    tk.Button(
        actions, text="SAVE CHANGES" if editing else "SAVE GAME",
        command=save_game, bg=orange, fg="white",
        font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2"
    ).pack(side="right", ipadx=18, ipady=9)
    tk.Button(
        actions, text="Cancel", command=window.destroy, bg="#F4F7FA", fg=text,
        font=("Segoe UI", 10), relief="flat", cursor="hand2"
    ).pack(side="left", ipadx=18, ipady=9)
    window.bind("<Return>", save_game)
    window.bind("<Escape>", lambda event: window.destroy())
    fields["title"].focus_set()
    return window
