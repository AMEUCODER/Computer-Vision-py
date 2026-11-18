"""FaceBlur command line and optional desktop entry point.

Examples:
    python main.py                         # open the desktop app
    python main.py photos/ -o blurred/     # process a folder
    python main.py image.jpg --strength 71 --sensitivity Sensitive
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from . import blur
except ImportError:  # direct execution from this folder
    import blur


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect and blur faces in images.")
    parser.add_argument("input", nargs="?", help="Image path or folder of images")
    parser.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent / "output"),
                        help="Output directory (default: face_blur/output)")
    parser.add_argument("--strength", type=int, default=51, help="Gaussian blur kernel strength (11-151; odd values preferred)")
    parser.add_argument("--sensitivity", choices=list(blur.SENSITIVITY), default="Balanced",
                        help="Face detection threshold preset")
    parser.add_argument("--recursive", action="store_true", help="Include subfolders")
    return parser


def _images(source: Path, recursive: bool) -> list[Path]:
    if source.is_file():
        if source.suffix.lower() not in blur.IMAGE_EXTS:
            raise SystemExit(f"Unsupported image format: {source.suffix}")
        return [source]
    if not source.is_dir():
        raise SystemExit(f"Input does not exist: {source}")
    iterator = source.rglob("*") if recursive else source.iterdir()
    return sorted(p for p in iterator if p.is_file() and p.suffix.lower() in blur.IMAGE_EXTS)


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        try:
            if __package__:
                from .gui import App
            else:
                from gui import App
        except ModuleNotFoundError as exc:
            if exc.name == "customtkinter":
                raise SystemExit("The FaceBlur desktop app needs CustomTkinter. Install it with: pip install customtkinter")
            raise
        App().mainloop()
        return

    args = _parser().parse_args(argv)
    if not args.input:
        _parser().error("provide an image/folder or run without arguments to open the desktop app")
    if args.strength < 1 or args.strength > 301:
        _parser().error("--strength must be between 1 and 301")
    source = Path(args.input).expanduser()
    files = _images(source, args.recursive)
    if not files:
        raise SystemExit(f"No supported images found in: {source}")
    output = Path(args.output).expanduser()
    threshold = blur.SENSITIVITY[args.sensitivity]
    results = blur.process_images([str(p) for p in files], str(output),
                                  ksize=args.strength, threshold=threshold)
    good = sum(err is None for _, _, err, _ in results)
    failed = len(results) - good
    face_count = sum(count for _, count, err, _ in results if err is None)
    print(f"FaceBlur: {good} saved, {failed} failed, {face_count} face(s) blurred")
    print(f"Output: {output.resolve()}")
    for name, count, err, out_path in results:
        if err:
            print(f"FAIL {name}: {err}", file=sys.stderr)
        else:
            print(f"OK   {name}: {count} face(s) -> {out_path}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
