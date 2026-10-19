# Air Draw

Draw in the air with your index finger, tracked live by MediaPipe and rendered with OpenCV. No mouse, stylus or touchscreen.

## Gestures

| Gesture | Action |
|---|---|
| Only index finger up | Draw |
| Index + middle finger up | Erase |
| Closed fist | Clear the whole canvas |

Press `q` to quit.

## Setup

```bash
pip install opencv-python mediapipe==0.10.21 numpy
python main.py
```

`mediapipe==0.10.21` is required because this project uses the legacy `mp.solutions` API.

## Project structure

```
Air-Draw/
├── main.py        # camera loop (run this)
├── detection.py   # MediaPipe hand tracking + gesture classification
├── canvas.py      # persistent drawing surface + blending
├── config.py      # every tunable number
└── README.md
```

## How it works

1. MediaPipe tracks 21 hand landmarks per frame (on a half-size copy of the frame for speed, see `DETECTION_SCALE`).
2. The bend angle at each finger's middle joint decides "up" or "curled". Using the angle instead of a y-coordinate comparison makes it work at any hand rotation.
3. Which fingers are up selects the mode: draw, erase or clear.
4. The index fingertip position is smoothed with an exponential moving average (`SMOOTHING`) and used to draw a line on a persistent canvas, which is blended over the live feed every frame.
5. A short tracking loss (up to `MISS_GRACE_FRAMES`) doesn't break the line, so fast movement doesn't leave gaps.

## Tuning (`config.py`)

| Setting | Effect |
|---|---|
| `BRUSH_THICKNESS`, `ERASER_THICKNESS`, `DRAW_COLOR` | Pen look (color is BGR) |
| `SMOOTHING` | 0 = raw and jittery, closer to 1 = smooth but laggy |
| `DETECTION_SCALE` | Lower = faster, higher = better for small or distant hands |
| `MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE` | Lower = fewer dropped frames, shakier landmarks |
| `EXTEND_ANGLE_THRESHOLD` | Cutoff angle between finger "up" and "curled" |

## Ideas for what to build on this

The same landmark-and-geometry building blocks can drive other outputs:

- **Gesture volume:** map the thumb-tip to index-tip distance (landmarks 4 and 8) to a 0-100 volume with `numpy.interp`, then set system volume (`pycaw` on Windows, `osascript` on macOS, `amixer` or `pulsectl` on Linux).
- **Gesture mouse:** map the index fingertip inside a central region of the frame to screen coordinates with `pyautogui`, smooth it, and use a pinch below a distance threshold to click.
