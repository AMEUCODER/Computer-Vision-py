# Hand Gesture Filter Camera

A live webcam app that tracks your hand with MediaPipe and switches image filters based on how many fingers you hold up. Hold one finger for a few seconds and it takes a photo after a countdown, and you can record video on demand.

## Features

- Real-time hand tracking with a 21-landmark skeleton overlay
- Finger-count-controlled filters (see the table below)
- Hands-free photo: hold up **1 finger for 5 seconds**, then a 5-second on-screen countdown runs and the photo saves automatically
- Video recording: press `f` to start or stop
- Debounced gesture detection so filters don't flicker on one noisy frame

## Finger count -> filter

| Fingers | Filter | How it works |
|---|---|---|
| 0 (fist) | None | Normal feed |
| 1 | Sobel edge magnitude | Grayscale gradient image (`apply_sharpen_filter` in `filters.py`) |
| 2 | Edge detection | `filter_edges` |
| 3 | Thermal / heatmap | `filter_thermal` (grayscale mapped to a color map) |
| 4 | Color invert | `filter_invert` |
| 5 (open palm) | None | Normal feed |

`filters.py` also contains `filter_gray`, `filter_sepia` and `blur_face` (Haar-cascade face blur). They are not mapped to a finger count by default, so you can wire them into `get_filters()` yourself.

> Holding **1 finger** is dual-purpose: it applies filter 1 immediately, and holding it for 5 seconds also starts the photo countdown. To separate them, change `TRIGGER_FINGER_COUNT` in `capture.py`.

## Controls

| Action | How |
|---|---|
| Switch filter | Hold up the matching number of fingers |
| Take a photo | Hold **1 finger for 5 seconds**, then wait out the 5-second countdown |
| Start / stop recording | Press `f` |
| Quit | Press `q` |

## Setup

```bash
pip install opencv-python mediapipe==0.10.21 numpy
python main.py
```

`mediapipe==0.10.21` is required because this project uses the legacy `mp.solutions` API.

## Project structure

```
HandVision-filters/
├── main.py          # camera loop, debouncing, ties everything together (run this)
├── fingercount.py   # MediaPipe hand tracking + finger counting
├── filters.py       # filter functions + the finger-count -> filter map
├── capture.py       # hold-to-trigger photo countdown + video recording
└── README.md
```

Photos are saved to `captures/photos/photo_<timestamp>.png` and videos to `captures/videos/video_<timestamp>.mp4`. Both folders are created automatically and are git-ignored.

## Customizing

- **Add a filter:** write `def my_filter(frame): ...` in `filters.py` (BGR frame in, BGR frame out) and add it to the dict in `get_filters()`.
- **Change the photo trigger:** edit `TRIGGER_FINGER_COUNT`, `HOLD_TRIGGER_SECONDS` and `COUNTDOWN_SECONDS` in `capture.py`.
- **Change debounce strictness:** edit `DEBOUNCE_FRAMES` in `main.py`.
- **Change detection sensitivity:** edit `min_detection_confidence` and `min_tracking_confidence` in `fingercount.py`.

## Troubleshooting

- **`module 'mediapipe' has no attribute 'solutions'`:** install `mediapipe==0.10.21`.
- **No hand detected:** use good lighting and keep your whole hand in frame.
- **Filters flicker:** raise `DEBOUNCE_FRAMES`.
- **Photo countdown starts by accident:** raise `HOLD_TRIGGER_SECONDS` or use a different `TRIGGER_FINGER_COUNT`.
- **Video won't open in your player:** change the `mp4v` fourcc in `capture.py` to `XVID` and the extension to `.avi`.
