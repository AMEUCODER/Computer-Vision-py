# Background Outpainter

Extend the plain / white studio background of your photos to any resolution you choose, for many photos at once, from a dark-themed desktop window. No command-line arguments needed.

Your original photo is never cropped or changed. The new area around it is filled with a smooth continuation of the background that matches its color, gradient and grain.

## Features

- Select many photos at once (or a whole folder) and process them in one run
- Live preview of the result before you start, with a dashed outline showing where your original photo sits
- Resolution presets (Reels / TikTok 9:16, Instagram 1:1 and 4:5, YouTube 16:9, 4K, Shopify 1:1, A4 print) or your own width and height
- Photo position (center, top, bottom, left, right) and adjustable edge blend
- Photo list with resolution, file size and per-file status (waiting, working, done, error)
- Progress bar, activity log, Stop button and an "Open output folder" button
- Dark theme with a sharp display on high-DPI Windows screens; fits 1366x768 laptop screens

## Files

| File | What it does |
|------|--------------|
| `main.py` | Entry point. Run this to open the window. |
| `interface.py` | The dark-themed Tkinter window: photo list, live preview, settings, progress. |
| `outpaint.py` | The outpainting logic. No UI, so you can import it in other scripts. |

Keep the three files in the same folder.

## Install

Requires Python 3.9+ with Tkinter (included with the standard Python installer on Windows and macOS).

```bash
pip install opencv-python numpy
```

On Linux, if Tkinter is missing: `sudo apt install python3-tk`

## Run

```bash
python main.py
```

## How to use

1. **Photos**: click *Add photos* and select as many as you want (hold Ctrl or Shift), or *Add folder* to add every image in a folder. Use *Remove* (selected rows) or *Clear all* to fix the list. Click a row to see it in the live preview.
2. **Output settings**:
   - **Preset** or type your own **Size**. Typing switches the preset to *Custom*, and *swap* flips width and height.
   - **Photo position**: where the original sits on the new canvas. Use *Bottom* if you want empty space above the product, for example for text.
   - **Edge blend**: softness of the seam between the original and the new area.
   - **Match film grain**: adds noise that matches the original background so the new area does not look too smooth.
   - **Save to**: click *Browse* to choose the output folder.
3. Click **Start processing**. The list shows each file's status as it finishes. Click **Stop** to stop after the current photo, and **Open output folder** to see the results.

Results are saved as `originalname_WIDTHxHEIGHT.ext` (for example `desk_1080x1920.jpg`). Your original files are never overwritten.

## Use it from your own code

```python
import outpaint

outpaint.process_file("photo.jpg", "out_folder", 1080, 1920, anchor="bottom")
```

Parameters of `process_file(src, out_dir, width, height, anchor="center", feather=12, grain=True)`:

- `anchor`: `center`, `top`, `bottom`, `left` or `right`
- `feather`: softness of the seam in pixels, higher means a smoother blend
- `grain`: match the noise of the original background

## Notes and limits

- Supported formats: JPG, PNG, WebP, BMP, TIFF.
- If a photo is larger than the target resolution, it is scaled down to fit. It is never cropped.
- File paths with Arabic or other non-English characters work on Windows.
- This method works best on plain or softly graded backgrounds (white studio shots, product photos). If the product touches the edge of the photo, or the background has a hard shadow or pattern, the new area will continue those edge colors and may look streaky or gray. The live preview shows this before you process anything.
- The preview is a small, fast approximation. The saved files are rendered at the full resolution you chose.
- For complex backgrounds you need a generative AI outpainting model (for example Stable Diffusion inpainting), which usually needs a GPU. This tool does not use one.
