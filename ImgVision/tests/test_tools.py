from PIL import Image
import numpy as np
import pytest

from engine.base_tool import ToolContext
from engine.runner import _argument_parser
from adjust.tool import AdjustTool
from auto_enhance.tool import AutoEnhanceTool
from blur.tool import BlurTool
from crop.tool import CropTool
from rotate_flip.tool import RotateFlipTool
from outpainting.outpaint import outpaint
from WaterMark.addWatermark import add_text_watermark
from WaterMark.logoWatermark import add_logo_watermark
from WaterMark.removeWatermark import remove_watermark


@pytest.fixture
def sample_rgba():
    return Image.new("RGBA", (240, 160), (120, 130, 140, 100))


def test_core_adjustments_preserve_transparency(sample_rgba):
    adjusted = AdjustTool().run(sample_rgba, {"brightness": 1.2, "contrast": 1.0,
                                               "saturation": 1.0, "warmth": 5}, ToolContext())
    enhanced = AutoEnhanceTool().run(sample_rgba, {"contrast_cutoff": 1.0,
                                                    "color": 1.1, "sharpness": 1.1}, ToolContext())
    for result in (adjusted, enhanced):
        assert result.mode == "RGBA"
        assert result.getchannel("A").getpixel((0, 0)) == 100


def test_blur_modes_return_same_size(sample_rgba):
    tool = BlurTool()
    for mode in ("whole", "background"):
        result = tool.run(sample_rgba, {"mode": mode, "strength": 4}, ToolContext())
        assert result.size == sample_rgba.size


def test_crop_aspect_ratio_and_rotation(sample_rgba):
    cropped = CropTool().run(sample_rgba, {"aspect": "9:16", "zoom": 1.0,
                                            "offset_x": 0, "offset_y": 0}, ToolContext())
    rotated = RotateFlipTool().run(sample_rgba, {"turn": "90", "flip_h": False,
                                                  "flip_v": False}, ToolContext())
    assert cropped.size == (90, 160)
    assert rotated.size == (160, 240)


def test_runner_exposes_expected_cli_options():
    parser = _argument_parser(CropTool)
    parsed = parser.parse_args(["photo.png", "--aspect", "9:16", "--zoom", "1.5", "--offset-x", "20"])
    assert parsed.aspect == "9:16"
    assert parsed.zoom == 1.5
    assert parsed.offset_x == 20


def test_outpaint_returns_requested_canvas():
    source = np.zeros((80, 120, 3), dtype=np.uint8)
    result = outpaint(source, 180, 140, anchor="bottom")
    assert result.shape == (140, 180, 3)


def test_watermark_operations_return_same_canvas():
    source = Image.new("RGB", (120, 80), "#dddddd")
    text_result = add_text_watermark(source, "Test", color="#fff")
    logo = Image.new("RGBA", (30, 15), (255, 0, 0, 120))
    logo_result = add_logo_watermark(source, logo)
    removed = remove_watermark(source, (10, 10, 35, 35))
    assert text_result.size == logo_result.size == removed.size == source.size


def test_watermark_rejects_invalid_rectangle():
    with pytest.raises(ValueError):
        remove_watermark(Image.new("RGB", (40, 40)), (30, 30, 10, 10))
