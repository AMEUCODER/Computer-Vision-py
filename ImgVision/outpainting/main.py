"""Entry point: run `python main.py` to open the Background Outpainter window."""
import sys
import tkinter as tk


def _enable_hidpi():
    """Keep the window sharp on high-DPI Windows screens."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def main():
    _enable_hidpi()
    from interface import App
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
