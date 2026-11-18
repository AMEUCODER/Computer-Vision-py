from __future__ import annotations
from typing import Any

from PIL import Image
from engine.base_tool import BaseTool, ToolContext
from engine.schemas.requests import ParamSpec


class RotateFlipTool(BaseTool):
    name = "rotate_flip"
    label = "Rotate & Flip"
    description = "Rotate an image by 90-degree increments and flip it horizontally or vertically."
    params = [
        ParamSpec("turn", "Rotate", "choice", "0", choices=("0", "90", "180", "270")),
        ParamSpec("flip_h", "Flip horizontally", "bool", False),
        ParamSpec("flip_v", "Flip vertically", "bool", False),
    ]

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        turn = int(params.get("turn", 0)) % 360
        if turn not in (0, 90, 180, 270):
            raise ValueError("turn must be 0, 90, 180, or 270")
        result = image
        rotations = {90: Image.Transpose.ROTATE_90, 180: Image.Transpose.ROTATE_180,
                     270: Image.Transpose.ROTATE_270}
        if turn:
            result = result.transpose(rotations[turn])
        if params.get("flip_h", False):
            result = result.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if params.get("flip_v", False):
            result = result.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return result
