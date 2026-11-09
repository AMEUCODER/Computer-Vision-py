"""All six image tools in one place.

    python run_tool.py                       -> window with a tool picker
    python run_tool.py list                  -> list the tools
    python run_tool.py blur photo.jpg --mode background --strength 15
    python run_tool.py adjust photos/ --brightness 1.2 --warmth 10 -o edited/
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
