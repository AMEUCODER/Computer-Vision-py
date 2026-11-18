from __future__ import annotations
from typing import Any
from PIL import Image, ImageEnhance, ImageOps
from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class AutoEnhanceTool(BaseTool):
    name = "auto_enhance"
    label = "Auto Enhance"
    description = "Automatically improves tonal contrast, color, and sharpness."
    params = [
        ParamSpec("contrast_cutoff", "Contrast cutoff percent", "slider", 1.0, min=0, max=5, step=0.5),
        ParamSpec("color", "Color", "slider", 1.1, min=0.5, max=2.0, step=0.05),
        ParamSpec("sharpness", "Sharpness", "slider", 1.1, min=0.5, max=2.5, step=0.05),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A") if ("A" in image.getbands() or "transparency" in image.info) else None
        rgb = ImageOps.autocontrast(image.convert("RGB"), cutoff=float(params.get("contrast_cutoff", 1.0)))
        rgb = ImageEnhance.Color(rgb).enhance(float(params.get("color", 1.1)))
        rgb = ImageEnhance.Sharpness(rgb).enhance(float(params.get("sharpness", 1.1)))
        if alpha is not None:
            rgb.putalpha(alpha)
        return rgb
