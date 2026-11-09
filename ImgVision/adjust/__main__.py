"""Run this tool on its own:

    python -m adjust photo.jpg [options]     (from the ImgVision folder)
    python adjust photo.jpg [options]        (same thing)
    python -m adjust                         no arguments = open the window
    python -m adjust --help                  see every option
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # make the shared 'engine' folder importable

from engine.runner import run_single
from adjust.tool import AdjustTool

run_single(AdjustTool)
