# ImgVision - standalone tools

Every tool now runs **on its own**, in two ways:

* **No arguments = a window** (customtkinter, or Tk for `outpainting`)
* **With arguments = command line**, no window, great for many photos at once (`--help` on any tool lists its options)

Install once: `pip install -r requirements.txt`  (Python 3.9+; on Linux also `sudo apt install python3-tk`)

## The six single-purpose tools (adjust, auto_enhance, blur, crop, face_blur, rotate_flip)

These came from the big project and needed its `engine`. A small stand-in `engine/` folder is included, so keep `engine/`
next to the tool folders. Run from this folder:

```bash
python run_tool.py                                   # one window with a tool picker
python run_tool.py list                              # list the tools
python -m blur photo.jpg --mode background --strength 15
python -m adjust photos/ --brightness 1.2 --warmth 10 -o edited/
python -m crop photo.jpg --aspect 9:16 --zoom 1.5 --offset-x 20
python -m rotate_flip photo.jpg --turn 90 --flip-h
python -m auto_enhance photo.jpg
python -m face_blur photos/ --sensitivity Sensitive --strength 40
python -m blur            # just this tool's window
```
Each tool accepts files and/or folders, and `-o` for an output folder (or a file name for a single photo).
Window: live preview, "Show original" switch, Save, and "Process a whole folder".

Background blur uses MediaPipe's selfie model (downloaded once, ~250 KB). Without MediaPipe or internet it falls back to a rougher OpenCV GrabCut mask.

## The other projects

| Folder | Window | Command line |
|---|---|---|
| `BlurFaces/` (Haar detector) and `face_blur_app/` (newer YuNet detector, use this one) | `python main.py` | `python main.py photos/ -o blurred/ --strength 71 --sensitivity Sensitive` |
| `outpainting/` | `python main.py` | `python main.py photo.jpg --size 1080x1920 --anchor bottom` (or `--preset reels`) |
| `WaterMark/` | `python main.py` | `python main.py text photo.jpg --text "(c) Me"`, `logo ... --logo logo.png`, `remove ... --box L T R B` |
| `picture_filter_project/` (pictures) | key-driven viewer: `python main.py` | `python main.py photos/ --filter anime -o out/` , `--list` |
| `FILTERS/` (live webcam) | `python main.py` (N/P switch filter, S save, Q quit) | `python main.py --filter crown`, `--image me.jpg --filter anime -o me.jpg` |
| `test/image_editor.py` | OpenCV sliders | `python image_editor.py photo.jpg --brightness 20 -o out.png` |

## What was fixed

* `blur`, `adjust`, `crop`, `auto_enhance`, `face_blur`, `rotate_flip`: no longer depend on the big project (`engine/` stand-in, own CLI + window).
* `FILTERS`: was broken (`filters.py` referenced filters that did not exist, duplicate keys, undefined `face_cascade`, and
  `mediapipe.solutions` was removed from new MediaPipe). Now uses the working filter set from `picture_filter_project`, with live switching.
* `BlurFaces`, `face_blur_app`: window code moved to `gui.py`; `main.py` now decides between window and command line.
* `WaterMark`: command line added, short hex colours (`#fff`) no longer crash, `--font` for Arabic text; the removal helper is now reachable.
* All image reading/writing that could touch Arabic paths uses `imdecode`/`imencode`.
