"""Run this tool on its own:

    python -m blur photo.jpg [options]     (from the ImgVision folder)
    python blur photo.jpg [options]        (same thing)
    python -m blur                         no arguments = open the window
    python -m blur --help                  see every option
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # make the shared 'engine' folder importable

from engine.runner import run_single
from blur.tool import BlurTool

run_single(BlurTool)
