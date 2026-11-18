from __future__ import annotations
from typing import Any
import numpy as np
import cv2
from PIL import Image, ImageFilter
from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class BlurTool(BaseTool):
    name = "blur"
    label = "Blur"
    description = "Blur the full image or soften the background while keeping the central subject sharper."
    params = [
        ParamSpec("mode", "Mode", "choice", "whole", choices=("whole", "background")),
        ParamSpec("strength", "Strength", "slider", 10, min=1, max=50, step=1),
    ]

    @staticmethod
    def _subject_mask(image: Image.Image) -> Image.Image:
        """Estimate a foreground mask with GrabCut; it is a fallback, not person recognition."""
        rgb = np.asarray(image.convert("RGB"))
        height, width = rgb.shape[:2]
        if width < 8 or height < 8:
            return Image.new("L", image.size, 255)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        mask = np.zeros((height, width), np.uint8)
        margin_x = max(1, int(width * 0.12))
        margin_y = max(1, int(height * 0.06))
        rect = (margin_x, margin_y, max(2, width - 2 * margin_x), max(2, height - 2 * margin_y))
        bg_model = np.zeros((1, 65), np.float64)
        fg_model = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(bgr, mask, rect, bg_model, fg_model, 4, cv2.GC_INIT_WITH_RECT)
            foreground = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
            result = Image.fromarray(foreground, mode="L").filter(ImageFilter.GaussianBlur(3))
            return result
        except cv2.error:
            # A soft central oval is a conservative fallback for tiny or pathological images.
            fallback = Image.new("L", image.size, 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(fallback)
            draw.ellipse((width * 0.18, height * 0.04, width * 0.82, height * 0.98), fill=255)
            return fallback.filter(ImageFilter.GaussianBlur(max(2, min(width, height) // 40)))

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        strength = float(params.get("strength", 10))
        blurred = image.filter(ImageFilter.GaussianBlur(radius=strength))
        if params.get("mode", "whole") == "whole":
            return blurred
        mask = self._subject_mask(image)
        # White mask preserves the subject; black mask uses the blurred background.
        return Image.composite(image, blurred, mask)
