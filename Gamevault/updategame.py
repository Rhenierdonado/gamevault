import sqlite3
from tkinter import messagebox

from addgame import open_game_form
from database import get_game, update_game_details


def open_update_game(parent, game_id, on_saved):
    try:
        game = get_game(game_id)
    except sqlite3.Error as error:
        messagebox.showerror("Database Error", str(error), parent=parent)
        return
    if game is None:
        messagebox.showwarning(
            "Game Unavailable", "This game is no longer available. Refresh the list.",
            parent=parent
        )
        return

    def save_details(title, platform, genre, release_year):
        return update_game_details(game_id, title, platform, genre, release_year)

    return open_game_form(parent, on_saved, save_details, game=game)
