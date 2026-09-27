"""Fan-Mate GUI launcher."""

import tkinter as tk

from fanmate.app import App


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
