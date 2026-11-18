"""Base contracts shared by the standalone ImgVision tools."""
from dataclasses import dataclass, field
from typing import Any, Dict

from PIL import Image


@dataclass
class ToolContext:
    """Runtime services passed to each tool. Models are optional by design."""
    models: Dict[str, Any] = field(default_factory=dict)


class BaseTool:
    name = "tool"
    label = "Image Tools"
    description = ""
    params = []

    def run(self, image: Image.Image, params: dict[str, Any], ctx: ToolContext) -> Image.Image:
        raise NotImplementedError
