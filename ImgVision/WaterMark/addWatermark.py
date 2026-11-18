"""Text watermarking helpers."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _font(font_path: str | None, size: int):
    if font_path:
        return ImageFont.truetype(font_path, size=size)
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def parse_color(value: str, opacity: int = 180) -> tuple[int, int, int, int]:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
        if len(raw) == 3:
            raw = "".join(ch * 2 for ch in raw)
        if len(raw) != 6:
            raise ValueError("Color must be #RGB or #RRGGBB")
        try:
            rgb = tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError as exc:
            raise ValueError("Invalid hexadecimal color") from exc
    else:
        color = Image.new("RGB", (1, 1), raw)
        rgb = color.getpixel((0, 0))
    return (*rgb, max(0, min(255, int(opacity))))


def add_text_watermark(image: Image.Image, text: str, *, font_path: str | None = None,
                       font_size: int | None = None, color: str = "#ffffff",
                       opacity: int = 160, position: str = "bottom-right",
                       margin: int = 28) -> Image.Image:
    if not text:
        raise ValueError("Watermark text cannot be empty")
    base = image.convert("RGBA")
    size = font_size or max(18, round(min(base.size) * 0.045))
    font = _font(font_path, size)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fill = parse_color(color, opacity)
    try:
        bbox = draw.textbbox((0, 0), text, font=font, direction="rtl" if any("\u0600" <= c <= "\u06ff" for c in text) else None)
    except (TypeError, ValueError):
        bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    positions = {
        "top-left": (margin - bbox[0], margin - bbox[1]),
        "top-right": (base.width - margin - tw - bbox[0], margin - bbox[1]),
        "bottom-left": (margin - bbox[0], base.height - margin - th - bbox[1]),
        "bottom-right": (base.width - margin - tw - bbox[0], base.height - margin - th - bbox[1]),
        "center": ((base.width - tw) // 2 - bbox[0], (base.height - th) // 2 - bbox[1]),
    }
    if position not in positions:
        raise ValueError(f"Unknown position: {position}")
    kwargs = {"font": font, "fill": fill}
    if any("\u0600" <= c <= "\u06ff" for c in text):
        kwargs["direction"] = "rtl"
    try:
        draw.text(positions[position], text, **kwargs)
    except (TypeError, ValueError):
        kwargs.pop("direction", None)
        draw.text(positions[position], text, **kwargs)
    return Image.alpha_composite(base, overlay)
