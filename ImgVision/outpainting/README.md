# Background Outpainter

Extend a plain or softly graded photo background to a new canvas size. The tool includes a dark Tkinter desktop interface and a command-line batch mode.

## Requirements

Install the project dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

Tkinter is included with standard Windows/macOS Python installers. On some Linux distributions, install it separately (for example, `sudo apt install python3-tk`).

## Desktop app

From the project root:

```bash
python outpainting/main.py
```

The UI supports photo selection, folder import, live preview, presets/custom dimensions, photo anchoring, edge blend, grain matching, batch progress, and cancellation after the current image.

## Command-line use

```bash
python outpainting/main.py photo.jpg --size 1080x1920 --anchor bottom -o out/
python outpainting/main.py photos/ --preset reels -o out/
python outpainting/main.py photos/ --size 1080x1350 --anchor center --recursive -o out/
```

Presets: `reels`, `story`, `square`, `portrait`, and `landscape`. Custom sizes are written as `WIDTHxHEIGHT`. Supported anchors are `center`, `top`, `bottom`, `left`, and `right`.

## Implementation notes

`outpaint.py` contains the image-processing logic and can be imported independently. It builds a smooth background field from pixels along the source image's outer edges, blends the edge residual into the new canvas, and optionally matches background grain. It does not use a generative model and cannot reconstruct a subject or object that is cut off at the source image boundary.

The source image is never overwritten. Results are named `originalname_WIDTHxHEIGHT.ext`; an index is added if a file with that name already exists.
