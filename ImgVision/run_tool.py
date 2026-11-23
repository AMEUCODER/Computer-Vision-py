"""Launch ImgVision's tool picker, image tools, or document converters."""
from adjust.tool import AdjustTool
from auto_enhance.tool import AutoEnhanceTool
from blur.tool import BlurTool
from crop.tool import CropTool
from face_blur.tool import FaceBlurTool
from rotate_flip.tool import RotateFlipTool

TOOLS = [AdjustTool, AutoEnhanceTool, BlurTool, CropTool, FaceBlurTool, RotateFlipTool]


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["convert"]:
        from converters.main import main
        raise SystemExit(main(sys.argv[2:]))
    if sys.argv[1:2] == ["word2pdf"]:
        from word2pdf.main import main
        main()
    from engine.runner import run_all
    run_all(TOOLS)
