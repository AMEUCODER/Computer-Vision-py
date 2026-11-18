"""Adapter that exposes the standalone FaceBlur engine to the ImgVision picker."""
from __future__ import annotations
from typing import Any
from PIL import Image
from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec
from . import blur as face_engine


class FaceBlurTool(BaseTool):
    name = "face_blur"
    label = "Face Blur"
    description = "Detect and blur faces to protect privacy."
    params = [
        ParamSpec("sensitivity", "Sensitivity", "choice", "Balanced", choices=tuple(face_engine.SENSITIVITY)),
        ParamSpec("strength", "Blur strength", "slider", 51, min=11, max=151, step=2),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        import numpy as np
        import cv2
        rgb = np.asarray(image.convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        threshold = face_engine.SENSITIVITY[params.get("sensitivity", "Balanced")]
        processed, _ = face_engine.blur_face(bgr, int(params.get("strength", 51)), threshold)
        result = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
        if "A" in image.getbands() or "transparency" in image.info:
            result.putalpha(image.convert("RGBA").getchannel("A"))
        return result
