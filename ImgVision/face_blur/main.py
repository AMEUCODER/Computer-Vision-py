"""FaceBlur - pick images (or a folder), faces get blurred, results go to ./output

Run:  python main.py
"""
import os
import queue
import threading
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps

import blur

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# (light, dark) colour pairs - CustomTkinter switches automatically with the theme
ACCENT = "#6366F1"
ACCENT_HOVER = "#4F46E5"
BG = ("#F3F4F8", "#0D0F14")
PANEL = ("#FFFFFF", "#151821")
CARD = ("#F3F4F9", "#1C202B")
BORDER = ("#E3E5EC", "#262B38")
TEXT = ("#111827", "#F3F4F6")
MUTED = ("#6B7280", "#8A93A8")

BADGES = {  # state: (text colour, background)
    "pending": (MUTED, ("#E8EAF0", "#262B38")),
    "working": (("#4338CA", "#A5B4FC"), ("#E0E7FF", "#272A52")),
    "faces": (("#15803D", "#4ADE80"), ("#DCFCE7", "#12301F")),
    "none": (("#B45309", "#FBBF24"), ("#FEF3C7", "#352A0E")),
    "error": (("#B91C1C", "#F87171"), ("#FEE2E2", "#3A1416")),
}


def shorten(s, n):
    return s if len(s) <= n else s[:n // 2 - 1] + "…" + s[-(n // 2):]


def make_thumb(path, size=60):
    try:
        im = Image.open(path)
        im.draft("RGB", (size * 3, size * 3))  # fast JPEG decode
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = ImageOps.fit(im, (size * 2, size * 2))
    except Exception:
        im = Image.new("RGB", (size * 2, size * 2), (60, 64, 78))
    return ctk.CTkImage(light_image=im, dark_image=im, size=(size, size))


class ImageRow(ctk.CTkFrame):
    def __init__(self, master, path, on_remove):
        super().__init__(master, fg_color=CARD, corner_radius=12)
        self.path, self.state = path, "pending"
        self.columnconfigure(1, weight=1)

        self._img = make_thumb(path)
        self.thumb = ctk.CTkLabel(self, text="", image=self._img, width=60, height=60)
        self.thumb.grid(row=0, column=0, rowspan=2, padx=(10, 12), pady=10)

        self.name = ctk.CTkLabel(self, text=shorten(os.path.basename(path), 46), anchor="w",
                                 font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT)
        self.name.grid(row=0, column=1, sticky="sw", pady=(12, 0))
        self.sub = ctk.CTkLabel(self, text=shorten(os.path.dirname(path), 60), anchor="w",
                                font=ctk.CTkFont(size=11), text_color=MUTED)
        self.sub.grid(row=1, column=1, sticky="nw", pady=(0, 12))

        self.badge = ctk.CTkFrame(self, width=98, height=28, corner_radius=14)
        self.badge.pack_propagate(False)
        self.badge.grid(row=0, column=2, rowspan=2, padx=8)
        self.badge_text = ctk.CTkLabel(self.badge, text="", fg_color="transparent",
                                       font=ctk.CTkFont(size=12, weight="bold"))
        self.badge_text.place(relx=0.5, rely=0.5, anchor="center")
        self.remove_btn = ctk.CTkButton(self, text="✕", width=30, height=30, corner_radius=8,
                                        fg_color="transparent", hover_color=BORDER, text_color=MUTED,
                                        command=lambda: on_remove(self))
        self.remove_btn.grid(row=0, column=3, rowspan=2, padx=(0, 10))
        self.set_state("pending", "Pending")

    def set_state(self, kind, text):
        fg, bg = BADGES[kind]
        self.badge.configure(fg_color=bg)
        self.badge_text.configure(text=text, text_color=fg)

    def show_result(self, out_path):
        self._img = make_thumb(out_path)
        self.thumb.configure(image=self._img)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("FaceBlur")
        self.geometry("1020x700")
        self.minsize(880, 580)
        self.configure(fg_color=BG)
        self.rows = []
        self.busy = False
        self.events = queue.Queue()
        self._load_queue = []

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    # ------------------------------------------------------------ layout
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=PANEL)
        sb.grid(row=0, column=0, sticky="nsw")
        sb.grid_propagate(False)
        sb.pack_propagate(False)

        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.pack(anchor="w", padx=24, pady=(28, 0))
        ctk.CTkLabel(logo, text="Face", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(logo, text="Blur", font=ctk.CTkFont(size=26, weight="bold"), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(sb, text="Protect privacy in one click.", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(anchor="w", padx=24, pady=(0, 24))

        ctk.CTkButton(sb, text="+  Add images", height=44, corner_radius=12, fg_color=ACCENT,
                      hover_color=ACCENT_HOVER, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.add_files).pack(fill="x", padx=24)
        ctk.CTkButton(sb, text="Add folder", height=44, corner_radius=12, fg_color="transparent",
                      border_width=1, border_color=BORDER, hover_color=CARD, text_color=TEXT,
                      font=ctk.CTkFont(size=14), command=self.add_folder).pack(fill="x", padx=24, pady=(10, 0))

        ctk.CTkLabel(sb, text="BLUR STRENGTH", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=MUTED).pack(anchor="w", padx=24, pady=(34, 6))
        self.strength = ctk.CTkSlider(sb, from_=11, to=151, number_of_steps=70, progress_color=ACCENT,
                                      button_color=ACCENT, button_hover_color=ACCENT_HOVER,
                                      command=self._strength_changed)
        self.strength.set(51)
        self.strength.pack(fill="x", padx=24)
        self.strength_lbl = ctk.CTkLabel(sb, text="", font=ctk.CTkFont(size=12), text_color=MUTED)
        self.strength_lbl.pack(anchor="w", padx=24, pady=(6, 0))
        self._strength_changed(51)

        ctk.CTkLabel(sb, text="DETECTION", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=MUTED).pack(anchor="w", padx=24, pady=(26, 6))
        self.sens = ctk.CTkSegmentedButton(sb, values=list(blur.SENSITIVITY), selected_color=ACCENT,
                                           selected_hover_color=ACCENT_HOVER, fg_color=CARD,
                                           unselected_color=CARD, unselected_hover_color=BORDER)
        self.sens.set("Balanced")
        self.sens.pack(fill="x", padx=24)
        ctk.CTkLabel(sb, text="Strict: fewer false blurs\nSensitive: catches more faces",
                     font=ctk.CTkFont(size=11), text_color=MUTED, justify="left").pack(anchor="w", padx=24, pady=(6, 0))

        ctk.CTkLabel(sb, text="APPEARANCE", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=MUTED).pack(anchor="w", padx=24, pady=(26, 6))
        theme = ctk.CTkSegmentedButton(sb, values=["Dark", "Light"], selected_color=ACCENT,
                               selected_hover_color=ACCENT_HOVER, fg_color=CARD,
                               unselected_color=CARD, unselected_hover_color=BORDER,
                               command=lambda v: ctk.set_appearance_mode(v.lower()))
        theme.pack(fill="x", padx=24)
        theme.set("Dark")

        bottom = ctk.CTkFrame(sb, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=24, pady=24)
        ctk.CTkLabel(bottom, text="Saved to", font=ctk.CTkFont(size=11), text_color=MUTED).pack(anchor="w")
        ctk.CTkLabel(bottom, text=shorten(OUTPUT_DIR, 34), font=ctk.CTkFont(size=12), text_color=TEXT,
                     anchor="w").pack(anchor="w", pady=(0, 10))
        ctk.CTkButton(bottom, text="Open output folder", height=36, corner_radius=10, fg_color=CARD,
                      hover_color=BORDER, text_color=TEXT, command=self.open_output).pack(fill="x")

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=26, pady=24)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        head = ctk.CTkFrame(main, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(head, text="Images", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT).pack(side="left")
        self.count_lbl = ctk.CTkLabel(head, text="0 images", text_color=MUTED, font=ctk.CTkFont(size=13))
        self.count_lbl.pack(side="left", padx=12, pady=(4, 0))
        self.clear_btn = ctk.CTkButton(head, text="Clear all", width=84, height=30, corner_radius=8,
                                       fg_color="transparent", hover_color=BORDER, text_color=MUTED,
                                       command=self.clear)
        self.clear_btn.pack(side="right")

        self.panel = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=18, border_width=1, border_color=BORDER)
        self.panel.grid(row=1, column=0, sticky="nsew")
        self.scroll = ctk.CTkScrollableFrame(self.panel, fg_color="transparent", corner_radius=18)
        self.scroll.pack(fill="both", expand=True, padx=6, pady=6)

        self.empty = ctk.CTkFrame(self.panel, fg_color="transparent")
        circle = ctk.CTkFrame(self.empty, width=72, height=72, corner_radius=26, fg_color=CARD)
        circle.pack()
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text="+", text_color=ACCENT, fg_color="transparent",
                     font=ctk.CTkFont(size=34, weight="bold")).place(relx=0.5, rely=0.46, anchor="center")
        ctk.CTkLabel(self.empty, text="No images yet", font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=TEXT).pack(pady=(14, 2))
        ctk.CTkLabel(self.empty, text="Add images or a whole folder to get started.",
                     font=ctk.CTkFont(size=13), text_color=MUTED).pack()
        self.empty.place(relx=0.5, rely=0.5, anchor="center")

        foot = ctk.CTkFrame(main, fg_color="transparent")
        foot.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        foot.columnconfigure(0, weight=1)
        self.status = ctk.CTkLabel(foot, text="Ready.", anchor="w", font=ctk.CTkFont(size=13),
                                   text_color=MUTED)
        self.status.grid(row=0, column=0, sticky="w")
        self.progress = ctk.CTkProgressBar(foot, height=8, progress_color=ACCENT, fg_color=BORDER)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 16))
        self.go_btn = ctk.CTkButton(foot, text="Blur faces", width=170, height=48, corner_radius=14,
                                    fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                    font=ctk.CTkFont(size=15, weight="bold"), command=self.start)
        self.go_btn.grid(row=0, column=1, rowspan=2)

    # ------------------------------------------------------------ list handling
    def _strength_changed(self, v):
        k = int(round(v))
        k += 1 - k % 2  # kernel size must be odd
        label = "Light" if k < 41 else "Medium" if k < 81 else "Strong" if k < 121 else "Maximum"
        self.strength_lbl.configure(text="%s  ·  %d" % (label, k))

    def _kernel(self):
        k = int(round(self.strength.get()))
        return k + 1 - k % 2

    def _update_count(self):
        n = len(self.rows) + len(self._load_queue)
        self.count_lbl.configure(text="%d image%s" % (n, "" if n == 1 else "s"))
        if self.rows or self._load_queue:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.5, anchor="center")

    def add_paths(self, paths):
        have = {r.path for r in self.rows} | set(self._load_queue)
        new = [p for p in paths if p not in have]
        self._load_queue += new
        self._update_count()
        if new and len(self._load_queue) == len(new):
            self._load_chunk()

    def _load_chunk(self):  # build rows a few at a time so the window never freezes
        for _ in range(6):
            if not self._load_queue:
                break
            row = ImageRow(self.scroll, self._load_queue.pop(0), self.remove_row)
            row.pack(fill="x", pady=4, padx=4)
            self.rows.append(row)
        self._update_count()
        if self._load_queue:
            self.after(5, self._load_chunk)

    def add_files(self):
        exts = " ".join("*" + e for e in sorted(blur.IMAGE_EXTS))
        files = filedialog.askopenfilenames(title="Choose images", filetypes=[("Images", exts), ("All files", "*.*")])
        self.add_paths(list(files))

    def add_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder of images")
        if folder:
            found = blur.images_in_folder(folder)
            if found:
                self.add_paths(found)
            else:
                self.status.configure(text="No images found in that folder.", text_color=BADGES["none"][0])

    def remove_row(self, row):
        if self.busy:
            return
        self.rows.remove(row)
        row.destroy()
        self._update_count()

    def clear(self):
        if self.busy:
            return
        self._load_queue.clear()
        for r in self.rows:
            r.destroy()
        self.rows = []
        self.progress.set(0)
        self.status.configure(text="Ready.", text_color=MUTED)
        self._update_count()

    def open_output(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(OUTPUT_DIR)  # noqa
            elif os.uname().sysname == "Darwin":
                os.system('open "%s"' % OUTPUT_DIR)
            else:
                os.system('xdg-open "%s"' % OUTPUT_DIR)
        except Exception:
            self.status.configure(text="Output folder: " + OUTPUT_DIR, text_color=MUTED)

    # ------------------------------------------------------------ processing (background thread)
    def start(self):
        if self.busy or self._load_queue:
            return
        todo = [r for r in self.rows if r.state != "done"]
        if not todo:
            msg = "Add some images first." if not self.rows else "All images are already blurred - add more or clear the list."
            self.status.configure(text=msg, text_color=BADGES["none"][0])
            return
        self.busy = True
        self.go_btn.configure(state="disabled", text="Working…")
        self.progress.set(0)
        self.status.configure(text="Starting…", text_color=MUTED)
        todo[0].set_state("working", "Working…")
        threading.Thread(target=self._work, args=(todo, self._kernel(), blur.SENSITIVITY[self.sens.get()]),
                         daemon=True).start()
        self._poll()

    def _work(self, todo, k, threshold):
        # Worker thread: never touch widgets here, only post messages to the queue.
        def prog(i, total, name, faces, out_path, err):
            self.events.put(("progress", todo, i, total, name, faces, out_path, err))

        try:
            results = blur.process_images([r.path for r in todo], OUTPUT_DIR, k, prog, threshold)
        except Exception as e:  # noqa
            results = [("?", 0, str(e), None)]
        self.events.put(("done", results))

    def _poll(self):  # main thread: apply queued updates to the UI
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "progress":
                    self._on_progress(*ev[1:])
                else:
                    self._done(ev[1])
        except queue.Empty:
            pass
        if self.busy:
            self.after(50, self._poll)

    def _on_progress(self, todo, i, total, name, faces, out_path, err):
        row = todo[i - 1]
        if err:
            row.state = "error"
            row.set_state("error", "Failed")
            row.sub.configure(text=shorten(err, 60), text_color=BADGES["error"][0])
        else:
            row.state = "done"
            row.set_state("faces" if faces else "none", "%d face%s" % (faces, "" if faces == 1 else "s") if faces else "No face")
            if out_path:
                row.show_result(out_path)
        if i < total:
            todo[i].set_state("working", "Working…")
        self.progress.set(i / total)
        self.status.configure(text="Processing %d of %d  ·  %s" % (i, total, shorten(name, 40)), text_color=MUTED)

    def _done(self, results):
        self.busy = False
        self.go_btn.configure(state="normal", text="Blur faces")
        ok = [r for r in results if r[2] is None]
        faces = sum(r[1] for r in ok)
        bad = len(results) - len(ok)
        msg = "Done  ·  %d face%s blurred in %d image%s  ·  saved to output" % (
            faces, "" if faces == 1 else "s", len(ok), "" if len(ok) == 1 else "s")
        if bad:
            msg += "  ·  %d failed" % bad
        self.status.configure(text=msg, text_color=BADGES["faces"][0])


if __name__ == "__main__":
    App().mainloop()
