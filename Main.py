import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from BattleshipGUI import BattleshipGUI
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()
