"""Run this tool on its own:

    python -m auto_enhance photo.jpg [options]     (from the ImgVision folder)
    python auto_enhance photo.jpg [options]        (same thing)
    python -m auto_enhance                         no arguments = open the window
    python -m auto_enhance --help                  see every option
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # make the shared 'engine' folder importable

from engine.runner import run_single
from auto_enhance.tool import AutoEnhanceTool

run_single(AutoEnhanceTool)
