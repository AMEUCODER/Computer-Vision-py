"""
Tkinter user interface (dark theme).

Pick many photos, set the output resolution, see a live preview of the result,
choose the output folder and process everything in one go.
"""
import base64
import math
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2

import outpaint

FONT = "Segoe UI"

# ---------- colour palette ----------
C = {
    "bg": "#0a0e1c",        # window background
    "card": "#111830",      # card background
    "card2": "#18213f",     # raised elements
    "input": "#0c1226",     # inputs / lists
    "border": "#26305a",
    "text": "#e8ebf5",
    "muted": "#8b94b0",
    "accent": "#7c5cff",    # violet
    "accent_hi": "#9378ff",
    "accent2": "#22d3ee",   # cyan
    "ok": "#34d399",
    "err": "#f87171",
    "head_l": "#2a1b6b",    # header gradient (left)
    "head_r": "#0b3b57",    # header gradient (right)
}

PRESETS = {
    "Custom": None,
    "Reels / TikTok / Shorts  9:16  (1080 x 1920)": (1080, 1920),
    "Instagram post  1:1  (1080 x 1080)": (1080, 1080),
    "Instagram portrait  4:5  (1080 x 1350)": (1080, 1350),
    "YouTube / Full HD  16:9  (1920 x 1080)": (1920, 1080),
    "4K  16:9  (3840 x 2160)": (3840, 2160),
    "Shopify product  1:1  (2048 x 2048)": (2048, 2048),
    "A4 print 300 dpi  (2480 x 3508)": (2480, 3508),
}

ANCHOR_LABELS = [("Center", "center"), ("Top", "top"), ("Bottom", "bottom"),
                 ("Left", "left"), ("Right", "right")]


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def fmt_size(n):
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.1f} MB"
    return f"{max(n, 1) / 1024:.0f} KB"


class App:
    def __init__(self, root):
        self.root = root
        root.title("Background Outpainter")
        self.ui = max(1.0, root.winfo_fpixels("1i") / 96.0)   # HiDPI factor
        avail_h = root.winfo_screenheight() - self._px(80)    # leave room for the taskbar
        root.geometry(f"{self._px(1140)}x{min(self._px(830), avail_h)}")
        root.minsize(self._px(1020), min(self._px(700), avail_h))
        root.configure(bg=C["bg"])

        # preview size: shrinks on small screens so the footer buttons always fit
        self.PW = self._px(430)
        self.PH = max(self._px(150), min(self._px(300), avail_h - self._px(520)))
        self.msgs = queue.Queue()
        self.path_of = {}          # tree iid -> file path
        self.meta = {}             # tree iid -> (w, h, bytes)
        self._seq = 0
        self._cache = None         # cached preview source image
        self._prev_job = None
        self._prev_img = None
        self.running = False
        self.stop_evt = threading.Event()

        self.width_var = tk.StringVar(value="1080")
        self.height_var = tk.StringVar(value="1920")
        self.preset_var = tk.StringVar(value=list(PRESETS)[1])
        self.anchor_var = tk.StringVar(value="center")
        self.feather_var = tk.DoubleVar(value=12)
        self.grain_var = tk.BooleanVar(value=True)
        self.out_var = tk.StringVar(value=str(Path.home() / "outpainted"))

        self._setup_style()
        self._build_header()
        self._build_footer()      # packed at the bottom first so it is never clipped
        self._build_body()

        for v in (self.width_var, self.height_var):
            v.trace_add("write", self._on_size_change)
        self.anchor_var.trace_add("write", lambda *a: self._schedule_preview())
        self.grain_var.trace_add("write", lambda *a: self._schedule_preview())

        self._on_preset()
        self._render_preview()
        root.after(80, self._poll)
        root.after(50, self._dark_titlebar)

    # ------------------------------------------------------------------ helpers
    def _px(self, n):
        return int(n * getattr(self, "ui", 1.0))

    def _dark_titlebar(self):
        """Dark window title bar on Windows 10/11 (silently ignored elsewhere)."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            val = ctypes.c_int(1)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), 4)
        except Exception:
            pass

    # ------------------------------------------------------------------ style
    def _setup_style(self):
        r = self.root
        s = ttk.Style(r)
        s.theme_use("clam")

        r.option_add("*TCombobox*Listbox.background", C["input"])
        r.option_add("*TCombobox*Listbox.foreground", C["text"])
        r.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        r.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        r.option_add("*TCombobox*Listbox.font", (FONT, 10))

        s.configure(".", background=C["card"], foreground=C["text"], font=(FONT, 10),
                    bordercolor=C["border"], focuscolor=C["card"])

        field = dict(fieldbackground=C["input"], foreground=C["text"], insertcolor=C["text"],
                     bordercolor=C["border"], lightcolor=C["border"], darkcolor=C["border"],
                     padding=6)
        s.configure("TEntry", **field)
        s.configure("TSpinbox", arrowcolor=C["muted"], background=C["card2"], **field)
        s.configure("TCombobox", arrowcolor=C["text"], background=C["card2"], **field)
        for w in ("TEntry", "TSpinbox", "TCombobox"):
            s.map(w, bordercolor=[("focus", C["accent"])],
                  lightcolor=[("focus", C["accent"])], darkcolor=[("focus", C["accent"])])
        s.map("TCombobox", fieldbackground=[("readonly", C["input"])],
              foreground=[("readonly", C["text"])],
              selectbackground=[("readonly", C["input"])],
              selectforeground=[("readonly", C["text"])])

        # Buttons
        s.configure("Card.TButton", background=C["card2"], foreground=C["text"],
                    bordercolor=C["border"], lightcolor=C["card2"], darkcolor=C["card2"],
                    padding=(12, 6), relief="flat")
        s.map("Card.TButton", background=[("active", "#243059"), ("disabled", C["card"])],
              foreground=[("disabled", C["muted"])])
        s.configure("Accent.TButton", background=C["accent"], foreground="#ffffff",
                    bordercolor=C["accent"], lightcolor=C["accent"], darkcolor=C["accent"],
                    padding=(22, 10), font=(FONT, 11, "bold"), relief="flat")
        s.map("Accent.TButton",
              background=[("disabled", "#2c2750"), ("active", C["accent_hi"])],
              foreground=[("disabled", "#7d7aa3")],
              bordercolor=[("disabled", "#2c2750")])
        s.configure("Stop.TButton", background="#3a1c2a", foreground=C["err"],
                    bordercolor="#5a2a3d", lightcolor="#3a1c2a", darkcolor="#3a1c2a",
                    padding=(16, 10), font=(FONT, 10, "bold"))
        s.map("Stop.TButton", background=[("active", "#4d2335"), ("disabled", C["card"])],
              foreground=[("disabled", C["muted"])])

        # Position toggle buttons
        s.configure("Anchor.Toolbutton", background=C["input"], foreground=C["muted"],
                    bordercolor=C["border"], lightcolor=C["input"], darkcolor=C["input"],
                    padding=(11, 6), relief="flat", font=(FONT, 9, "bold"))
        s.map("Anchor.Toolbutton",
              background=[("selected", C["accent"]), ("active", C["card2"])],
              foreground=[("selected", "#ffffff"), ("active", C["text"])],
              bordercolor=[("selected", C["accent"])],
              lightcolor=[("selected", C["accent"])], darkcolor=[("selected", C["accent"])])

        # List
        s.configure("Treeview", background=C["input"], fieldbackground=C["input"],
                    foreground=C["text"], borderwidth=0, rowheight=self._px(30),
                    font=(FONT, 10))
        s.map("Treeview", background=[("selected", "#2c2570")],
              foreground=[("selected", "#ffffff")])
        s.configure("Treeview.Heading", background="#161e3a", foreground=C["muted"],
                    relief="flat", borderwidth=0, padding=(8, 7), font=(FONT, 9, "bold"))
        s.map("Treeview.Heading", background=[("active", "#1d2750")])
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        s.configure("Vertical.TScrollbar", background=C["card2"], troughcolor=C["input"],
                    bordercolor=C["input"], arrowcolor=C["muted"],
                    lightcolor=C["card2"], darkcolor=C["card2"], gripcount=0)
        s.map("Vertical.TScrollbar", background=[("active", "#2a3763")])

        s.configure("Horizontal.TScale", background=C["accent"], troughcolor=C["input"],
                    bordercolor=C["border"], lightcolor=C["accent"], darkcolor=C["accent"])
        s.configure("Accent.Horizontal.TProgressbar", troughcolor=C["input"],
                    background=C["accent"], bordercolor=C["border"],
                    lightcolor=C["accent2"], darkcolor=C["accent"], thickness=self._px(10))

    # ------------------------------------------------------------------ layout
    def _label(self, parent, text, muted=False, bold=False, size=10, **kw):
        return tk.Label(parent, text=text, bg=kw.pop("bg", C["card"]),
                        fg=C["muted"] if muted else C["text"],
                        font=(FONT, size, "bold" if bold else "normal"), **kw)

    def _card(self, parent, title, hint=""):
        outer = tk.Frame(parent, bg=C["border"])
        inner = tk.Frame(outer, bg=C["card"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        head = tk.Frame(inner, bg=C["card"])
        head.pack(fill="x", padx=14, pady=(12, 8))
        self._label(head, title, bold=True, size=11).pack(side="left")
        hint_lbl = self._label(head, hint, muted=True, size=9)
        hint_lbl.pack(side="right")
        body = tk.Frame(inner, bg=C["card"])
        body.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        return outer, body, hint_lbl

    def _build_header(self):
        h = self._px(76)
        self.header = tk.Canvas(self.root, height=h, highlightthickness=0, bd=0, bg=C["bg"])
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._draw_header)

    def _draw_header(self, event=None):
        c = self.header
        w, h = c.winfo_width(), self._px(76)
        c.delete("all")
        bands = 72
        for i in range(bands):
            x0, x1 = w * i // bands, w * (i + 1) // bands + 1
            c.create_rectangle(x0, 0, x1, h - 3, fill=_mix(C["head_l"], C["head_r"], i / (bands - 1)),
                               outline="")
        for i in range(bands):   # accent line
            x0, x1 = w * i // bands, w * (i + 1) // bands + 1
            c.create_rectangle(x0, h - 3, x1, h, fill=_mix(C["accent"], C["accent2"], i / (bands - 1)),
                               outline="")
        c.create_text(self._px(26), h // 2 - self._px(10), anchor="w", text="Background Outpainter",
                      fill="#ffffff", font=(FONT, 20, "bold"))
        c.create_text(self._px(28), h // 2 + self._px(16), anchor="w",
                      text="Extend plain studio backgrounds to any resolution  -  batch mode",
                      fill="#b9c3e6", font=(FONT, 10))
        c.create_text(w - self._px(26), h // 2, anchor="e", text="Match edges  |  Match grain  |  No cropping",
                      fill="#9fb0d9", font=(FONT, 9))

    def _build_body(self):
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=self._px(20), pady=(self._px(12), 0))
        body.columnconfigure(0, weight=5, uniform="c")
        body.columnconfigure(1, weight=4, uniform="c")
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, self._px(8)))
        right = tk.Frame(body, bg=C["bg"])
        right.grid(row=0, column=1, sticky="nsew", padx=(self._px(8), 0))

        self._build_log(left)       # packed at the bottom first so it is never squeezed out
        self._build_photos(left)
        self._build_preview(right)
        self._build_settings(right)

    # ---- photos card
    def _build_photos(self, parent):
        card, body, self.stats_lbl = self._card(parent, "1  Photos", "0 photos")
        card.pack(fill="both", expand=True)

        bar = tk.Frame(body, bg=C["card"])
        bar.pack(fill="x", pady=(0, 8))
        self.add_btn = ttk.Button(bar, text="+  Add photos", style="Card.TButton", command=self.add_files)
        self.add_btn.pack(side="left")
        self.addf_btn = ttk.Button(bar, text="Add folder", style="Card.TButton", command=self.add_folder)
        self.addf_btn.pack(side="left", padx=6)
        self.rem_btn = ttk.Button(bar, text="Remove", style="Card.TButton", command=self.remove_selected)
        self.rem_btn.pack(side="left")
        self.clr_btn = ttk.Button(bar, text="Clear all", style="Card.TButton", command=self.clear)
        self.clr_btn.pack(side="left", padx=6)

        wrap = tk.Frame(body, bg=C["input"], highlightthickness=1, highlightbackground=C["border"])
        wrap.pack(fill="both", expand=True)
        cols = ("name", "dims", "size", "status")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="extended")
        for col, text, width, anchor, stretch in (
                ("name", "File", 250, "w", True), ("dims", "Resolution", 110, "center", False),
                ("size", "Size", 80, "e", False), ("status", "Status", 90, "center", False)):
            self.tree.heading(col, text=text, anchor="w" if col == "name" else anchor)
            self.tree.column(col, width=self._px(width), anchor=anchor, stretch=stretch, minwidth=self._px(60))
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.tag_configure("ok", foreground=C["ok"])
        self.tree.tag_configure("err", foreground=C["err"])
        self.tree.tag_configure("work", foreground=C["accent2"])
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._schedule_preview(60))

        self.empty_lbl = tk.Label(wrap, text="No photos yet\nClick  \"+  Add photos\"  to begin",
                                  bg=C["input"], fg=C["muted"], font=(FONT, 11), justify="center")
        self.empty_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # ---- log card
    def _build_log(self, parent):
        card, body, _ = self._card(parent, "Activity")
        card.pack(side="bottom", fill="x", pady=(self._px(14), 0))
        wrap = tk.Frame(body, bg=C["input"], highlightthickness=1, highlightbackground=C["border"])
        wrap.pack(fill="x")
        self.log = tk.Text(wrap, height=5, bg=C["input"], fg=C["muted"], bd=0, relief="flat",
                           font=("Consolas" if sys.platform == "win32" else "Courier", 9),
                           state="disabled", padx=8, pady=6, wrap="word",
                           insertbackground=C["text"], highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")
        self.log.tag_configure("ok", foreground=C["ok"])
        self.log.tag_configure("err", foreground=C["err"])
        self.log.tag_configure("info", foreground=C["accent2"])

    # ---- preview card
    def _build_preview(self, parent):
        card, body, _ = self._card(parent, "Live preview", "dashed line = original photo")
        card.pack(fill="x")
        self.prev_canvas = tk.Canvas(body, width=self.PW, height=self.PH, bg=C["input"],
                                     highlightthickness=1, highlightbackground=C["border"])
        self.prev_canvas.pack()
        self.prev_info = tk.Label(body, text="", bg=C["card"], fg=C["muted"], font=(FONT, 9),
                                  justify="left", anchor="w", wraplength=self.PW)
        self.prev_info.pack(fill="x", pady=(8, 0))

    # ---- settings card
    def _build_settings(self, parent):
        card, body, _ = self._card(parent, "2  Output settings")
        card.pack(fill="both", expand=True, pady=(self._px(14), 0))
        body.columnconfigure(1, weight=1)

        def row_label(r, text):
            self._label(body, text, muted=True, size=9).grid(row=r, column=0, sticky="w",
                                                             pady=6, padx=(0, 12))

        # preset
        row_label(0, "Preset")
        combo = ttk.Combobox(body, textvariable=self.preset_var, values=list(PRESETS), state="readonly")
        combo.grid(row=0, column=1, sticky="ew")
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_preset())

        # size
        row_label(1, "Size (px)")
        size = tk.Frame(body, bg=C["card"])
        size.grid(row=1, column=1, sticky="w")
        ttk.Spinbox(size, textvariable=self.width_var, from_=16, to=20000, increment=10, width=7).pack(side="left")
        self._label(size, "x", muted=True).pack(side="left", padx=6)
        ttk.Spinbox(size, textvariable=self.height_var, from_=16, to=20000, increment=10, width=7).pack(side="left")
        ttk.Button(size, text="swap", style="Card.TButton", width=5, command=self.swap_size).pack(side="left", padx=(10, 0))
        self.ratio_lbl = self._label(size, "", muted=True, size=9)
        self.ratio_lbl.pack(side="left", padx=10)

        # position
        row_label(2, "Photo position")
        pos = tk.Frame(body, bg=C["card"])
        pos.grid(row=2, column=1, sticky="w")
        for text, val in ANCHOR_LABELS:
            ttk.Radiobutton(pos, text=text, value=val, variable=self.anchor_var,
                            style="Anchor.Toolbutton").pack(side="left", padx=(0, 4))

        # edge blend
        row_label(3, "Edge blend")
        fe = tk.Frame(body, bg=C["card"])
        fe.grid(row=3, column=1, sticky="ew")
        self.feather_lbl = self._label(fe, "12 px", size=9)
        self.feather_lbl.pack(side="right", padx=(10, 0))
        ttk.Scale(fe, from_=0, to=60, variable=self.feather_var, orient="horizontal",
                  command=self._on_feather).pack(side="left", fill="x", expand=True)

        # grain
        row_label(4, "Options")
        tk.Checkbutton(body, text="Match film grain of the original background", variable=self.grain_var,
                       bg=C["card"], fg=C["text"], activebackground=C["card"], activeforeground=C["text"],
                       selectcolor=C["input"], highlightthickness=0, bd=0, font=(FONT, 10),
                       cursor="hand2").grid(row=4, column=1, sticky="w")

        # output
        row_label(5, "Save to")
        out = tk.Frame(body, bg=C["card"])
        out.grid(row=5, column=1, sticky="ew")
        ttk.Entry(out, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        ttk.Button(out, text="Browse", style="Card.TButton", command=self.choose_output).pack(side="left", padx=(6, 0))

    # ---- footer
    def _build_footer(self):
        foot = tk.Frame(self.root, bg=C["bg"])
        foot.pack(side="bottom", fill="x", padx=self._px(20), pady=self._px(12))
        left = tk.Frame(foot, bg=C["bg"])
        left.pack(side="left", fill="x", expand=True)
        self.status_lbl = tk.Label(left, text="Ready", bg=C["bg"], fg=C["muted"], font=(FONT, 10), anchor="w")
        self.status_lbl.pack(fill="x")
        self.progress = ttk.Progressbar(left, style="Accent.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x", pady=(6, 0), padx=(0, 18))

        self.start_btn = ttk.Button(foot, text="Start processing", style="Accent.TButton", command=self.start)
        self.stop_btn = ttk.Button(foot, text="Stop", style="Stop.TButton", command=self.stop, state="disabled")
        self.open_btn = ttk.Button(foot, text="Open output folder", style="Card.TButton", command=self.open_output)
        self.start_btn.pack(side="right")
        self.stop_btn.pack(side="right", padx=8)
        self.open_btn.pack(side="right")

    # ------------------------------------------------------------------ photo list
    def paths(self):
        return [self.path_of[i] for i in self.tree.get_children()]

    def _update_stats(self):
        n = len(self.tree.get_children())
        total = sum(m[2] for m in self.meta.values() if m)
        txt = f"{n} photo{'s' if n != 1 else ''}"
        if n and total:
            txt += f"  -  {fmt_size(total)}"
        self.stats_lbl.config(text=txt)
        if n:
            self.empty_lbl.place_forget()
        else:
            self.empty_lbl.place(relx=0.5, rely=0.5, anchor="center")

    def _add(self, new_paths):
        existing = set(self.path_of.values())
        added = []
        for p in new_paths:
            p = str(p)
            if p in existing:
                continue
            existing.add(p)
            self._seq += 1
            iid = f"i{self._seq}"
            self.path_of[iid] = p
            self.tree.insert("", "end", iid=iid, values=(Path(p).name, "...", "", "waiting"))
            added.append((iid, p))
        self._update_stats()
        if added:
            threading.Thread(target=self._load_meta, args=(added,), daemon=True).start()
            if not self.tree.selection():
                self.tree.selection_set(added[0][0])
            self._schedule_preview(60)

    def _load_meta(self, items):
        for iid, p in items:
            try:
                img = outpaint.read_image(p)
                h, w = img.shape[:2]
                self.msgs.put(("meta", iid, (w, h, os.path.getsize(p))))
            except Exception:
                self.msgs.put(("meta", iid, None))

    def add_files(self):
        exts = " ".join(f"*{e}" for e in sorted(outpaint.IMAGE_EXTS))
        paths = filedialog.askopenfilenames(title="Select photos",
                                            filetypes=[("Images", exts), ("All files", "*.*")])
        self._add(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder of photos")
        if folder:
            self._add(sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in outpaint.IMAGE_EXTS))

    def remove_selected(self):
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self.path_of.pop(iid, None)
            self.meta.pop(iid, None)
        self._update_stats()
        self._schedule_preview(60)

    def clear(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.path_of.clear()
        self.meta.clear()
        self._cache = None
        self._update_stats()
        self._schedule_preview(60)

    def choose_output(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.out_var.set(folder)

    def open_output(self):
        p = Path(self.out_var.get().strip() or ".")
        try:
            p.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            messagebox.showerror("Open folder", str(e))

    # ------------------------------------------------------------------ settings events
    def _size(self):
        try:
            w, h = int(self.width_var.get()), int(self.height_var.get())
        except ValueError:
            return None
        return (w, h) if 16 <= w <= 20000 and 16 <= h <= 20000 else None

    def _on_preset(self):
        size = PRESETS.get(self.preset_var.get())
        if size:
            self._setting_preset = True
            self.width_var.set(str(size[0]))
            self.height_var.set(str(size[1]))
            self._setting_preset = False
            self._on_size_change()

    def _on_size_change(self, *a):
        if not getattr(self, "_setting_preset", False):
            self.preset_var.set("Custom")
        size = self._size()
        if size:
            w, h = size
            g = math.gcd(w, h)
            self.ratio_lbl.config(text=f"ratio {w // g}:{h // g}" if max(w, h) // g <= 40
                                  else f"ratio {w / h:.2f}:1")
        else:
            self.ratio_lbl.config(text="")
        self._schedule_preview()

    def swap_size(self):
        w, h = self.width_var.get(), self.height_var.get()
        self.width_var.set(h)
        self.height_var.set(w)

    def _on_feather(self, value):
        self.feather_lbl.config(text=f"{int(float(value))} px")
        self._schedule_preview()

    # ------------------------------------------------------------------ preview
    def _schedule_preview(self, delay=250):
        if self._prev_job:
            self.root.after_cancel(self._prev_job)
        self._prev_job = self.root.after(delay, self._render_preview)

    def _preview_path(self):
        sel = self.tree.selection()
        if sel:
            return self.path_of.get(sel[0])
        kids = self.tree.get_children()
        return self.path_of.get(kids[0]) if kids else None

    def _preview_message(self, text):
        c = self.prev_canvas
        c.delete("all")
        c.create_text(self.PW // 2, self.PH // 2, text=text, fill=C["muted"],
                      font=(FONT, 11), justify="center")
        self.prev_info.config(text="")

    def _render_preview(self):
        self._prev_job = None
        path, size = self._preview_path(), self._size()
        if size is None:
            self._preview_message("Enter a width and height\nbetween 16 and 20000 px")
            return
        if path is None:
            self._preview_message("Add a photo to see\na live preview of the result")
            return
        W, H = size
        try:
            if self._cache is None or self._cache[0] != path:
                img = outpaint.read_image(path)
                if img is None:
                    raise ValueError("cannot read image")
                oh, ow = img.shape[:2]
                f0 = min(1.0, 1400 / max(ow, oh))
                if f0 < 1:
                    img = cv2.resize(img, (max(1, round(ow * f0)), max(1, round(oh * f0))),
                                     interpolation=cv2.INTER_AREA)
                self._cache = (path, img, ow, oh, f0)
            _, small, ow, oh, f0 = self._cache

            s = min(self.PW / W, self.PH / H)
            pw, ph = max(1, round(W * s)), max(1, round(H * s))
            sw, sh = max(1, round(ow * s)), max(1, round(oh * s))
            scaled = cv2.resize(small, (sw, sh),
                                interpolation=cv2.INTER_AREA if s < f0 else cv2.INTER_LINEAR)
            out = outpaint.outpaint(scaled, pw, ph, self.anchor_var.get(),
                                    max(1, round(self.feather_var.get() * s)), self.grain_var.get())
            ok, buf = cv2.imencode(".png", out)
            self._prev_img = tk.PhotoImage(data=base64.b64encode(buf.tobytes()))
        except Exception as e:
            self._preview_message(f"Preview unavailable\n{e}")
            return

        c = self.prev_canvas
        c.delete("all")
        cx, cy = self.PW // 2, self.PH // 2
        c.create_image(cx, cy, image=self._prev_img)
        x0, y0 = cx - pw // 2, cy - ph // 2

        # dashed outline of where the original photo sits
        k = min(1.0, pw / sw, ph / sh)
        dw, dh = max(1, round(sw * k)), max(1, round(sh * k))
        ax, ay = (pw - dw) // 2, (ph - dh) // 2
        a = self.anchor_var.get()
        ax, ay = (0 if a == "left" else pw - dw if a == "right" else ax,
                  0 if a == "top" else ph - dh if a == "bottom" else ay)
        c.create_rectangle(x0 + ax, y0 + ay, x0 + ax + dw, y0 + ay + dh,
                           outline=C["accent2"], dash=(4, 3))
        c.create_rectangle(x0, y0, x0 + pw - 1, y0 + ph - 1, outline=C["border"])

        pct = min(1.0, W / ow, H / oh) * 100
        self.prev_info.config(
            text=f"{ow} x {oh}  ->  {W} x {H} px   |   photo at {pct:.0f}%   |   {a}")

    # ------------------------------------------------------------------ processing
    def _set_busy(self, busy):
        self.running = busy
        state = "disabled" if busy else "normal"
        for b in (self.start_btn, self.add_btn, self.addf_btn, self.rem_btn, self.clr_btn):
            b.config(state=state)
        self.stop_btn.config(state="normal" if busy else "disabled")

    def start(self):
        files = [(i, self.path_of[i]) for i in self.tree.get_children()]
        if not files:
            messagebox.showwarning("No photos", "Add at least one photo first.")
            return
        size = self._size()
        if size is None:
            messagebox.showerror("Resolution", "Width and height must be whole numbers (16 - 20000).")
            return
        out_dir = self.out_var.get().strip()
        if not out_dir:
            messagebox.showerror("Output folder", "Choose an output folder.")
            return

        for iid, _ in files:
            self.tree.set(iid, "status", "waiting")
            self.tree.item(iid, tags=())
        self.stop_evt.clear()
        self._set_busy(True)
        self.progress.config(maximum=len(files), value=0)
        self.status_lbl.config(text=f"Processing 0 / {len(files)} ...", fg=C["text"])
        self._log(f"Started: {len(files)} photo(s) -> {size[0]} x {size[1]} px, saving to {out_dir}", "info")
        args = (files, out_dir, size[0], size[1], self.anchor_var.get(),
                int(self.feather_var.get()), self.grain_var.get())
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def stop(self):
        self.stop_evt.set()
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="Stopping after the current photo ...", fg=C["muted"])

    def _worker(self, files, out_dir, width, height, anchor, feather, grain):
        ok = 0
        for n, (iid, path) in enumerate(files, 1):
            if self.stop_evt.is_set():
                break
            self.msgs.put(("file", iid, "working", "work"))
            try:
                out = outpaint.process_file(path, out_dir, width, height, anchor, feather, grain)
                ok += 1
                self.msgs.put(("file", iid, "done", "ok"))
                self.msgs.put(("log", f"OK   {Path(path).name}  ->  {out.name}", "ok"))
            except Exception as e:
                self.msgs.put(("file", iid, "error", "err"))
                self.msgs.put(("log", f"FAIL {Path(path).name}: {e}", "err"))
            self.msgs.put(("step", n, len(files)))
        self.msgs.put(("done", ok, len(files), out_dir, self.stop_evt.is_set()))

    def _poll(self):
        try:
            while True:
                msg = self.msgs.get_nowait()
                kind = msg[0]
                if kind == "meta":
                    _, iid, data = msg
                    if iid in self.path_of:
                        self.meta[iid] = data
                        if data:
                            self.tree.set(iid, "dims", f"{data[0]} x {data[1]}")
                            self.tree.set(iid, "size", fmt_size(data[2]))
                        else:
                            self.tree.set(iid, "dims", "unreadable")
                        self._update_stats()
                elif kind == "file":
                    _, iid, text, tag = msg
                    if iid in self.path_of:
                        self.tree.set(iid, "status", text)
                        self.tree.item(iid, tags=(tag,))
                elif kind == "log":
                    self._log(msg[1], msg[2])
                elif kind == "step":
                    _, n, total = msg
                    self.progress.config(value=n)
                    self.status_lbl.config(text=f"Processing {n} / {total} ...", fg=C["text"])
                elif kind == "done":
                    _, ok, total, out_dir, stopped = msg
                    self._set_busy(False)
                    word = "Stopped" if stopped else "Finished"
                    self.status_lbl.config(text=f"{word}: {ok} of {total} saved to {out_dir}",
                                           fg=C["ok"] if ok == total else C["err"] if ok == 0 else C["text"])
                    self._log(f"{word}: {ok}/{total} saved in {out_dir}", "info")
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def _log(self, text, tag=""):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")
