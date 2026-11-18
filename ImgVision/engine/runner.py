"""CLI and lightweight Tkinter runner shared by all ImgVision tools."""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps

from .base_tool import ToolContext

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _read_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.load()
        return image.copy()


def _save_image(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")
        image.save(path, quality=95, optimize=True)
    else:
        image.save(path)


def _iter_inputs(source: Path, recursive: bool) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(f"Input does not exist: {source}")
    iterator = source.rglob("*") if recursive else source.iterdir()
    return sorted(p for p in iterator if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def _output_path(src: Path, output: Path | None, tool_name: str, multiple: bool) -> Path:
    if output is None:
        return src.with_name(f"{src.stem}_{tool_name}{src.suffix}")
    if not multiple and output.suffix.lower() in IMAGE_EXTS:
        return output
    destination = output / f"{src.stem}_{tool_name}{src.suffix}"
    if not multiple or not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    index = 1
    while (output / f"{stem}_{index}{suffix}").exists():
        index += 1
    return output / f"{stem}_{index}{suffix}"


def _argument_parser(tool_cls) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=tool_cls.description or tool_cls.label)
    parser.add_argument("input", nargs="?", help="Image path or folder of images")
    parser.add_argument("-o", "--output", help="Output image path (single input) or output folder")
    parser.add_argument("--recursive", action="store_true", help="Include subfolders when input is a folder")
    for spec in tool_cls.params:
        flag = "--" + spec.name.replace("_", "-")
        help_text = spec.help or spec.label
        if spec.kind == "choice":
            parser.add_argument(flag, choices=list(spec.choices), default=spec.default, help=help_text)
        elif spec.kind == "bool":
            if bool(spec.default):
                parser.add_argument(flag, dest=spec.name, action="store_false", help=f"Disable: {help_text}")
            else:
                parser.add_argument(flag, dest=spec.name, action="store_true", help=help_text)
        else:
            value_type = int if isinstance(spec.default, int) and not isinstance(spec.default, bool) else float
            parser.add_argument(flag, type=value_type, default=spec.default, help=help_text)
    return parser


def _validate_params(tool_cls, params: dict) -> None:
    for spec in tool_cls.params:
        if spec.name not in params:
            params[spec.name] = spec.default
        value = params[spec.name]
        if spec.kind == "slider":
            if spec.min is not None and value < spec.min:
                raise ValueError(f"--{spec.name.replace('_', '-')} must be at least {spec.min}")
            if spec.max is not None and value > spec.max:
                raise ValueError(f"--{spec.name.replace('_', '-')} must be at most {spec.max}")


def _process(tool_cls, image: Image.Image, params: dict) -> Image.Image:
    result = tool_cls().run(image, params, ToolContext())
    if not isinstance(result, Image.Image):
        raise TypeError(f"{tool_cls.label}.run() must return a PIL.Image.Image")
    return result


def run_single(tool_cls, argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _argument_parser(tool_cls)
    if not argv:
        _launch_tool_window(tool_cls)
        return
    args = parser.parse_args(argv)
    if not args.input:
        parser.error("provide an image/folder or run with no arguments to open the window")
    _validate_params(tool_cls, vars(args))
    source = Path(args.input).expanduser()
    output = Path(args.output).expanduser() if args.output else None
    files = _iter_inputs(source, args.recursive)
    if not files:
        raise SystemExit(f"No supported images found in: {source}")
    multiple = len(files) > 1 or source.is_dir()
    succeeded, failed = 0, 0
    for src in files:
        try:
            result = _process(tool_cls, _read_image(src), vars(args))
            destination = _output_path(src, output, tool_cls.name, multiple)
            _save_image(result, destination)
            succeeded += 1
            print(f"OK   {src} -> {destination}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {src}: {exc}", file=sys.stderr)
    print(f"{tool_cls.label}: {succeeded} saved, {failed} failed")
    if failed:
        raise SystemExit(1)


def run_all(tool_classes: Iterable[type]) -> None:
    tools = list(tool_classes)
    argv = sys.argv[1:]
    if argv and argv[0] == "list":
        for tool in tools:
            print(f"{tool.name:14} {tool.description}")
        return
    if argv and argv[0] in {tool.name for tool in tools}:
        tool = next(t for t in tools if t.name == argv[0])
        run_single(tool, argv[1:])
        return
    if argv:
        print("Usage: python run_tool.py [list | TOOL [IMAGE_OR_FOLDER] [OPTIONS]]", file=sys.stderr)
        print("Available tools: " + ", ".join(t.name for t in tools), file=sys.stderr)
        raise SystemExit(2)

    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("ImgVision")
    root.geometry("460x440")
    root.configure(bg="#111827")
    tk.Label(root, text="IMGVISION", bg="#111827", fg="#f9fafb",
             font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=28, pady=(24, 4))
    tk.Label(root, text="Choose an image tool", bg="#111827", fg="#9ca3af",
             font=("Segoe UI", 10)).pack(anchor="w", padx=30, pady=(0, 18))
    for tool in tools:
        tk.Button(root, text=f"{tool.label}  →", anchor="w", padx=16, pady=9,
                  bg="#1f2937", fg="#f9fafb", activebackground="#374151",
                  activeforeground="#ffffff", relief="flat", font=("Segoe UI", 10, "bold"),
                  command=lambda selected=tool: (root.destroy(), _launch_tool_window(selected))).pack(
                      fill="x", padx=28, pady=4)
    root.mainloop()


def _launch_tool_window(tool_cls) -> None:
    """Open a small Tk GUI; all image processing still uses the same tool class as the CLI."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class ToolWindow:
        def __init__(self, root):
            self.root = root
            self.image = None
            self.path = None
            self.preview_ref = None
            root.title(f"ImgVision · {tool_cls.label}")
            root.geometry("1420x720")
            root.configure(bg="#111827")
            header = tk.Frame(root, bg="#111827")
            header.pack(fill="x", padx=22, pady=(18, 10))
            tk.Label(header, text=tool_cls.label, bg="#111827", fg="white",
                     font=("Segoe UI", 19, "bold")).pack(anchor="w")
            tk.Label(header, text=tool_cls.description, bg="#111827", fg="#9ca3af",
                     wraplength=700, justify="left").pack(anchor="w", pady=(4, 0))
            top = tk.Frame(root, bg="#1f2937")
            top.pack(fill="both", expand=True, padx=22, pady=8)
            self.preview = tk.Label(top, text="Open an image to preview", bg="#1f2937", fg="#9ca3af")
            self.preview.pack(fill="both", expand=True, padx=12, pady=12)
            self.controls = tk.Frame(root, bg="#111827")
            self.controls.pack(fill="x", padx=22, pady=8)
            self.variables = {}
            for spec in tool_cls.params:
                line = tk.Frame(self.controls, bg="#111827")
                line.pack(fill="x", pady=3)
                tk.Label(line, text=spec.label, width=18, anchor="w", bg="#111827", fg="#e5e7eb").pack(side="left")
                if spec.kind == "choice":
                    var = tk.StringVar(value=spec.default)
                    widget = ttk.Combobox(line, textvariable=var, values=list(spec.choices), state="readonly", width=22)
                    widget.pack(side="left")
                    widget.bind("<<ComboboxSelected>>", lambda _event: self.update_preview())
                elif spec.kind == "bool":
                    var = tk.BooleanVar(value=bool(spec.default))
                    widget = tk.Checkbutton(line, variable=var, bg="#111827", fg="#e5e7eb",
                                            selectcolor="#1f2937", activebackground="#111827",
                                            command=self.update_preview)
                    widget.pack(side="left")
                else:
                    var = tk.DoubleVar(value=float(spec.default))
                    scale = tk.Scale(line, variable=var, from_=spec.min or 0,
                                     to=spec.max if spec.max is not None else 100,
                                     resolution=spec.step or 1, orient="horizontal", length=300,
                                     bg="#111827", fg="#e5e7eb", highlightthickness=0,
                                     command=lambda _value: self.update_preview())
                    scale.pack(side="left")
                self.variables[spec.name] = var
            buttons = tk.Frame(root, bg="#111827")
            buttons.pack(fill="x", padx=22, pady=(8, 20))
            tk.Button(buttons, text="Open image", command=self.open_image, padx=14, pady=8).pack(side="left")
            tk.Button(buttons, text="Save result", command=self.save_result, padx=14, pady=8).pack(side="right")

        def params(self):
            values = {}
            for spec in tool_cls.params:
                value = self.variables[spec.name].get()
                if spec.kind == "slider" and isinstance(spec.default, int) and not isinstance(spec.default, bool):
                    value = int(round(value))
                values[spec.name] = value
            return values

        def open_image(self):
            selected = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"), ("All files", "*.*")])
            if not selected:
                return
            try:
                self.image = _read_image(Path(selected))
                self.path = Path(selected)
                self.update_preview()
            except Exception as exc:
                messagebox.showerror("Open image", str(exc))

        def update_preview(self):
            if self.image is None:
                return
            try:
                from PIL import ImageTk
                image = _process(tool_cls, self.image.copy(), self.params())
                image.thumbnail((650, 340))
                self.preview_ref = ImageTk.PhotoImage(image.convert("RGB"))
                self.preview.configure(image=self.preview_ref, text="")
            except Exception as exc:
                self.preview.configure(text=f"Preview error: {exc}", image="")

        def save_result(self):
            if self.image is None or self.path is None:
                messagebox.showinfo("Save result", "Open an image first.")
                return
            default = self.path.with_name(f"{self.path.stem}_{tool_cls.name}{self.path.suffix}")
            selected = filedialog.asksaveasfilename(initialfile=default.name,
                       defaultextension=self.path.suffix,
                       filetypes=[("Image", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff")])
            if not selected:
                return
            try:
                result = _process(tool_cls, self.image.copy(), self.params())
                _save_image(result, Path(selected))
                messagebox.showinfo("Saved", f"Saved to:\n{selected}")
            except Exception as exc:
                messagebox.showerror("Processing failed", str(exc))

    root = tk.Tk()
    ToolWindow(root)
    root.mainloop()
