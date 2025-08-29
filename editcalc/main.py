from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from .ui import PricingApp

def main() -> None:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.25)
    except tk.TclError:
        pass
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    PricingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
