"""Watermark command line: text, logo overlay, or selected-area inpainting."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from PIL import Image, ImageOps

try:
    from .addWatermark import add_text_watermark
    from .logoWatermark import add_logo_watermark
    from .removeWatermark import remove_watermark
except ImportError:  # direct execution: python main.py
    from addWatermark import add_text_watermark
    from logoWatermark import add_logo_watermark
    from removeWatermark import remove_watermark


def _read(path: Path) -> Image.Image:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.load()
        return image.copy()


def _write(image: Image.Image, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        rgba = image.convert("RGBA")
        base = Image.new("RGB", rgba.size, "white")
        base.paste(rgba, mask=rgba.getchannel("A"))
        base.save(path, quality=95)
    else:
        image.save(path)




def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Add a text/logo watermark or inpaint a selected area.")
    sub = parser.add_subparsers(dest="command", required=True)

    text_p = sub.add_parser("text", help="Add a text watermark")
    text_p.add_argument("image")
    text_p.add_argument("--text", required=True)
    text_p.add_argument("--font")
    text_p.add_argument("--size", type=int)
    text_p.add_argument("--color", default="#ffffff", help="Hex color, e.g. #fff or #ffffff")
    text_p.add_argument("--opacity", type=int, default=160)
    text_p.add_argument("--position", choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"], default="bottom-right")
    text_p.add_argument("--margin", type=int, default=28)
    text_p.add_argument("-o", "--output")

    logo_p = sub.add_parser("logo", help="Overlay a logo watermark")
    logo_p.add_argument("image")
    logo_p.add_argument("--logo", required=True)
    logo_p.add_argument("--scale", type=float, default=0.18, help="Logo width as a fraction of the image width")
    logo_p.add_argument("--opacity", type=int, default=180)
    logo_p.add_argument("--position", choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"], default="bottom-right")
    logo_p.add_argument("--margin", type=int, default=28)
    logo_p.add_argument("-o", "--output")

    remove_p = sub.add_parser("remove", help="Inpaint a rectangular region (works best on simple backgrounds)")
    remove_p.add_argument("image")
    remove_p.add_argument("--box", required=True, type=int, nargs=4, metavar=("L", "T", "R", "B"))
    remove_p.add_argument("--radius", type=int, default=3)
    remove_p.add_argument("--method", choices=["telea", "ns"], default="telea")
    remove_p.add_argument("-o", "--output")

    args = parser.parse_args(argv)
    source = Path(args.image).expanduser()
    if not source.is_file():
        parser.error(f"image does not exist: {source}")
    image = _read(source)
    if args.command == "text":
        result = add_text_watermark(image, args.text, font_path=args.font,
                                    font_size=args.size, color=args.color,
                                    opacity=args.opacity, position=args.position,
                                    margin=args.margin)
        suffix = "_watermarked"
    elif args.command == "logo":
        logo_path = Path(args.logo).expanduser()
        if not logo_path.is_file():
            parser.error(f"logo does not exist: {logo_path}")
        result = add_logo_watermark(image, _read(logo_path), scale=args.scale,
                                    opacity=args.opacity, position=args.position,
                                    margin=args.margin)
        suffix = "_logo"
    else:
        result = remove_watermark(image, args.box, radius=args.radius, method=args.method)
        suffix = "_cleaned"
    output = Path(args.output).expanduser() if args.output else source.with_name(source.stem + suffix + source.suffix)
    _write(result, output)
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
