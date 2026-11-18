"""Transparent logo overlay helpers."""
from __future__ import annotations
from PIL import Image


def add_logo_watermark(image: Image.Image, logo: Image.Image, *, scale: float = 0.18,
                       opacity: int = 180, position: str = "bottom-right",
                       margin: int = 28) -> Image.Image:
    if not 0.01 <= float(scale) <= 1.0:
        raise ValueError("scale must be between 0.01 and 1.0")
    base = image.convert("RGBA")
    mark = logo.convert("RGBA")
    target_w = max(1, round(base.width * scale))
    target_h = max(1, round(mark.height * target_w / mark.width))
    if target_h > base.height * 0.8:
        target_h = max(1, round(base.height * 0.8))
        target_w = max(1, round(mark.width * target_h / mark.height))
    mark = mark.resize((target_w, target_h), Image.Resampling.LANCZOS)
    if opacity < 255:
        alpha = mark.getchannel("A").point(lambda p: round(p * max(0, min(255, opacity)) / 255))
        mark.putalpha(alpha)
    positions = {
        "top-left": (margin, margin),
        "top-right": (base.width - target_w - margin, margin),
        "bottom-left": (margin, base.height - target_h - margin),
        "bottom-right": (base.width - target_w - margin, base.height - target_h - margin),
        "center": ((base.width - target_w) // 2, (base.height - target_h) // 2),
    }
    if position not in positions:
        raise ValueError(f"Unknown position: {position}")
    base.alpha_composite(mark, dest=positions[position])
    return base
