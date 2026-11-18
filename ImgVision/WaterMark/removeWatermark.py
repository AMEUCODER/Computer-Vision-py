"""Remove a selected rectangular overlay using OpenCV inpainting."""
from __future__ import annotations
import numpy as np
import cv2
from PIL import Image


def remove_watermark(image: Image.Image, box: tuple[int, int, int, int], *,
                     radius: int = 3, method: str = "telea") -> Image.Image:
    left, top, right, bottom = (int(v) for v in box)
    width, height = image.size
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(f"Box must satisfy 0 <= left < right <= {width} and 0 <= top < bottom <= {height}")
    if radius < 1 or radius > 100:
        raise ValueError("radius must be between 1 and 100")
    flags = {"telea": cv2.INPAINT_TELEA, "ns": cv2.INPAINT_NS}
    if method not in flags:
        raise ValueError("method must be 'telea' or 'ns'")
    rgb = np.asarray(image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[top:bottom, left:right] = 255
    result = cv2.inpaint(bgr, mask, float(radius), flags[method])
    return Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
