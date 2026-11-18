"""Launch ImgVision's tool picker or a specific image-processing tool.

Examples:
    python run_tool.py
    python run_tool.py list
    python run_tool.py blur photo.jpg --mode background --strength 15
    python run_tool.py crop photo.jpg --aspect 9:16 --zoom 1.5 --offset-x 20
"""
from adjust.tool import AdjustTool
from auto_enhance.tool import AutoEnhanceTool
from blur.tool import BlurTool
from crop.tool import CropTool
from face_blur.tool import FaceBlurTool
from rotate_flip.tool import RotateFlipTool

TOOLS = [AdjustTool, AutoEnhanceTool, BlurTool, CropTool, FaceBlurTool, RotateFlipTool]


if __name__ == "__main__":
    from engine.runner import run_all
    run_all(TOOLS)
