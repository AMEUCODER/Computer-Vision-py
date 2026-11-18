"""Background outpainting desktop app and command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import tkinter as tk

try:
    from . import outpaint
except ImportError:  # direct execution from this folder
    import outpaint

PRESETS = {"reels": (1080, 1920), "story": (1080, 1920), "square": (1080, 1080),
           "portrait": (1080, 1350), "landscape": (1920, 1080)}


def _enable_hidpi():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def _parse_size(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().replace("×", "x").split("x", 1)
        result = int(width), int(height)
    except Exception as exc:
        raise argparse.ArgumentTypeError("size must look like 1080x1920") from exc
    if min(result) < 1 or max(result) > 16000:
        raise argparse.ArgumentTypeError("width and height must be between 1 and 16000 pixels")
    return result


def _launch_gui():
    _enable_hidpi()
    try:
        if __package__:
            from .interface import App
        else:
            from interface import App
    except ImportError:
        raise
    root = tk.Tk()
    App(root)
    root.mainloop()


def main(argv: list[str] | None = None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        _launch_gui()
        return
    parser = argparse.ArgumentParser(description="Extend a plain background to a target canvas size.")
    parser.add_argument("input", help="Image path or folder of images")
    parser.add_argument("--size", type=_parse_size, help="Output dimensions, e.g. 1080x1920")
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Common social-media output size")
    parser.add_argument("--anchor", choices=outpaint.ANCHORS, default="center")
    parser.add_argument("--feather", type=int, default=12, help="Edge transition distance in pixels")
    parser.add_argument("--no-grain", action="store_true", help="Do not match the source photo's background grain")
    parser.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent / "output"),
                        help="Output directory")
    parser.add_argument("--recursive", action="store_true", help="Include subfolders")
    args = parser.parse_args(argv)
    if args.size and args.preset:
        parser.error("use either --size or --preset, not both")
    size = args.size or PRESETS.get(args.preset or "reels")
    if args.feather < 0 or args.feather > 300:
        parser.error("--feather must be between 0 and 300")
    source = Path(args.input).expanduser()
    if source.is_file():
        files = [source]
    elif source.is_dir():
        iterator = source.rglob("*") if args.recursive else source.iterdir()
        files = sorted(p for p in iterator if p.is_file() and p.suffix.lower() in outpaint.IMAGE_EXTS)
    else:
        parser.error(f"input does not exist: {source}")
        return
    if not files:
        raise SystemExit(f"No supported images found in: {source}")
    output = Path(args.output).expanduser()
    succeeded = failed = 0
    for path in files:
        try:
            saved = outpaint.process_file(path, output, size[0], size[1], args.anchor,
                                          args.feather, not args.no_grain)
            succeeded += 1
            print(f"OK   {path} -> {saved}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {path}: {exc}", file=sys.stderr)
    print(f"Outpainting: {succeeded} saved, {failed} failed in {size[0]}x{size[1]}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
