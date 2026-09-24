# Hand Gesture Filter Camera

A live webcam app that tracks your hand with MediaPipe, switches image
filters based on how many fingers you're holding up, auto-captures a
photo after you hold up one finger for a few seconds (Pixel-camera-style
countdown), and can record video on demand.

## Features

- **Real-time hand tracking** via MediaPipe (21-landmark skeleton overlay)
- **Finger-count-controlled filters**: fist, face blur, thermal look, edge
  detection, color invert
- **Hands-free photo capture**: hold up 1 finger for 5 seconds -> a
  5-second on-screen countdown appears -> photo is saved automatically
- **Video recording**: press `f` to start/stop recording the live feed
  to an `.mp4` file
- **Debounced gesture detection** so filters don't flicker from a single
  noisy frame

## Project Structure

```
.
├── main.py           # camera loop - ties everything together, run this
├── fingercount.py     # MediaPipe hand tracking + finger-counting logic
├── filters.py         # all image filter functions + finger->filter map
├── capture.py          # hold-to-trigger photo countdown + video recording
├── captures/
│   ├── photos/          # auto-saved photos land here
│   └── videos/           # recorded videos land here
└── README.md
```

## Setup

1. (Recommended) create and activate a virtual environment (version 3.12):
   ```
   python -m venv mp_env
   # Windows
   mp_env\Scripts\activate
   # macOS/Linux
   source mp_env/bin/activate
   ```

2. Install dependencies:
   ```
   pip install opencv-python mediapipe
   ```

3. Run it:
   ```
   python main.py
   ```

## Controls

| Action                           | How                                               |
|----------------------------------|---------------------------------------------------|
| Switch filter                    | Hold up the matching number of fingers (see table below) |
| Take a photo (hands-free)        | Hold up **1 finger for 5 seconds** -> wait out the 5s countdown |
| Start / stop video recording     | Press `f`                                         |
| Quit                             | Press `q`                                         |

## Finger Count -> Filter

| Fingers | Filter                             |
|---------|----------------------------------- |
| 0 (fist)| None (normal feed)                 |
| 1       | kermel                             |
| 2       | Thermal                            |
| 3       | Thermal / heatmap                  |
| 4       | Color invert                       |
| 5 (open palm) | None (normal feed)           |

> Note: holding up **1 finger** is dual-purpose - it applies the face-blur
> filter immediately, and if held continuously for 5 seconds it *also*
> triggers the photo countdown. This is intentional but can be changed by
> setting `TRIGGER_FINGER_COUNT` in `capture.py` to a different value than
> the one mapped to a filter in `filters.py`.

## Customizing

- **Add/change a filter**: write a new `def my_filter(frame): ...` function
  in `filters.py` (it must take a BGR frame and return a BGR frame), then
  add it to the dict returned by `get_filters()`.
- **Change which gesture triggers the photo timer**: edit
  `TRIGGER_FINGER_COUNT` in `capture.py`.
- **Change the hold duration or countdown length**: edit
  `HOLD_TRIGGER_SECONDS` and `COUNTDOWN_SECONDS` in `capture.py`.
- **Change how strict filter-switching debounce is**: edit
  `DEBOUNCE_FRAMES` in `main.py`.
- **Change detection sensitivity**: edit `min_detection_confidence` /
  `min_tracking_confidence` in `fingercount.py` (lower = more sensitive
  but more false positives).

## Output

- Photos save to `captures/photos/photo_<timestamp>.png`
- Videos save to `captures/videos/video_<timestamp>.mp4`
- Both folders are created automatically if they don't exist.

## Troubleshooting

- **No hand detected**: make sure you're well-lit and your whole hand is
  in frame; MediaPipe's model handles most lighting/background conditions
  well without any manual tuning.
- **Filters flicker between two values**: raise `DEBOUNCE_FRAMES` in
  `main.py`.
- **Photo countdown triggers by accident**: raise `HOLD_TRIGGER_SECONDS`
  in `capture.py`, or pick a less commonly-used finger count for
  `TRIGGER_FINGER_COUNT`.
- **Video file won't open**: some players don't support the `mp4v`
  fourcc codec - try changing it to `'XVID'` (and the file extension to
  `.avi`) in `capture.py` if this happens.
