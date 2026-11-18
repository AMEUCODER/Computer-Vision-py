# ImgVision

ImgVision is a collection of standalone image-processing tools. The tools share a small runtime, but each can also be run independently from this folder.

## Setup

Use Python 3.10 or newer. Install the core dependencies:

```bash
python -m pip install -r requirements.txt
```

`tkinter` is used for desktop windows and is included with most standard Python installations (Linux distributions may package it separately, for example `python3-tk`). `customtkinter` is needed only for the separate FaceBlur desktop interface; install it with `python -m pip install -r requirements-gui.txt`. FaceBlur's command-line mode does not require it.

## Open the app or list tools

```bash
python run_tool.py          # tool picker
python run_tool.py list      # list available tools
python run_tool.py adjust    # open the Adjust window
```

## Tools

| Tool | Desktop window | Command-line example |
|---|---|---|
| Adjust | `python -m adjust` | `python -m adjust photo.jpg --brightness 1.2 --warmth 10 -o edited.jpg` |
| Auto Enhance | `python -m auto_enhance` | `python -m auto_enhance photo.jpg -o enhanced.jpg` |
| Blur | `python -m blur` | `python -m blur photo.jpg --mode background --strength 15` |
| Crop | `python -m crop` | `python -m crop photo.jpg --aspect 9:16 --zoom 1.5 --offset-x 20` |
| Face Blur | `python -m face_blur` | `python -m face_blur photos/ -o blurred/ --strength 71 --sensitivity Sensitive` |
| Rotate & Flip | `python -m rotate_flip` | `python -m rotate_flip photo.jpg --turn 90 --flip-h` |
| Background Outpainting | `python outpainting/main.py` | `python outpainting/main.py photo.jpg --size 1080x1920 --anchor bottom` |
| Watermark | CLI subcommands | `python WaterMark/main.py text photo.jpg --text "(c) Me"` |

For the six tools in the picker, a folder can be supplied instead of a single image. Use `-o` to choose an output folder; `--recursive` also processes nested folders. If `-o` is an image filename for a single input, that exact file is used.

## Background outpainting

The outpainting tool extends plain backgrounds and supports common presets:

```bash
python outpainting/main.py photo.jpg --preset reels -o out/
python outpainting/main.py photos/ --size 1080x1350 --anchor center -o out/
```

It is designed for relatively simple backgrounds. It does not reconstruct missing parts of a subject that touch the source image's edge.

## Face Blur

The FaceBlur command-line tool accepts a single image or a folder. Sensitivity values are `Strict`, `Balanced`, and `Sensitive`. The YuNet detector model and Haar cascade are included in `face_blur/`. Install the requirements before running it.

## Watermark commands

```bash
python WaterMark/main.py text photo.jpg --text "© My Brand" --position bottom-right
python WaterMark/main.py logo photo.jpg --logo logo.png --scale 0.16
python WaterMark/main.py remove photo.jpg --box 20 30 220 100
```

Watermark removal uses OpenCV inpainting inside the selected rectangle. Results vary: it works best when the marked area is surrounded by a relatively simple background, and it cannot reliably reconstruct complex details hidden beneath a watermark.

## Notes

- Image loading applies EXIF orientation.
- The CLI supports common image formats: JPEG, PNG, WebP, BMP, and TIFF.
- The core tools do not require a GPU or cloud service.
