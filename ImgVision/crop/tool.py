from __future__ import annotations
from typing import Any

from PIL import Image
from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class CropTool(BaseTool):
    name = "crop"
    label = "Crop"
    description = "Crop to a common aspect ratio with zoom and horizontal/vertical positioning."
    params = [
        ParamSpec("aspect", "Aspect ratio", "choice", "free",
                  choices=("free", "1:1", "4:5", "3:4", "9:16", "16:9", "3:2", "2:3")),
        ParamSpec("zoom", "Zoom", "slider", 1.0, min=1.0, max=3.0, step=0.05),
        ParamSpec("offset_x", "Horizontal offset percent", "slider", 0, min=-100, max=100, step=1),
        ParamSpec("offset_y", "Vertical offset percent", "slider", 0, min=-100, max=100, step=1),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        width, height = image.size
        aspect = params.get("aspect", "free")
        if aspect == "free":
            base_w, base_h = width, height
        else:
            ratio = float(aspect.split(":")[0]) / float(aspect.split(":")[1])
            if width / height > ratio:
                base_h = height
                base_w = max(1, round(height * ratio))
            else:
                base_w = width
                base_h = max(1, round(width / ratio))

        zoom = float(params.get("zoom", 1.0))
        if zoom < 1.0:
            raise ValueError("zoom must be at least 1.0")
        crop_w = max(1, round(base_w / zoom))
        crop_h = max(1, round(base_h / zoom))
        max_left = width - crop_w
        max_top = height - crop_h
        offset_x = max(-100.0, min(100.0, float(params.get("offset_x", 0)))) / 100.0
        offset_y = max(-100.0, min(100.0, float(params.get("offset_y", 0)))) / 100.0
        left = round((width - crop_w) / 2 + offset_x * max_left / 2)
        top = round((height - crop_h) / 2 + offset_y * max_top / 2)
        left = max(0, min(width - crop_w, left))
        top = max(0, min(height - crop_h, top))
        result = image.crop((left, top, left + crop_w, top + crop_h))
        if (crop_w, crop_h) != (base_w, base_h):
            result = result.resize((base_w, base_h), Image.Resampling.LANCZOS)
        return result
