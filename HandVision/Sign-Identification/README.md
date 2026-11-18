# Sign Identification

Recognizes hand signs from a live webcam using MediaPipe hand landmarks and rule-based geometry. No training data and no model to train.

## Recognized signs

Fist, Open Palm, Thumbs Up, Thumbs Down, Thumb Out, Peace / Victory, Pointing, Rock On, Call Me, I Love You (ASL), OK Sign.

## Setup

```bash
pip install opencv-python mediapipe==0.10.21 numpy
python main.py
```

Press `q` to quit. `mediapipe==0.10.21` is required because this project uses the legacy `mp.solutions` API.

## Project structure

```
Sign-Identification/
├── main.py              # camera loop + smoothing (run this)
├── detection.py         # MediaPipe setup, finger states, sign classification
├── config.py            # every tunable number
├── sign_main.py         # older copy of main.py (safe to delete)
├── sign_identifier.py   # original single-file version (safe to delete)
└── README.md
```

`main.py` + `detection.py` + `config.py` are the current version. The other two files are earlier iterations kept for reference.

## How it works

1. MediaPipe returns 21 landmarks for the hand.
2. For each finger, the bend angle at the middle joint (PIP) is computed. Near 180 degrees means straight, much lower means curled. Because it uses an angle rather than a y-coordinate comparison, a sign held sideways or upside down is still recognized.
3. The five extended/curled flags, plus a few extra checks, are matched to signs in `classify_sign()`:
   - **OK Sign:** thumb tip and index tip closer than `OK_PINCH_DISTANCE`.
   - **Thumbs Up / Down:** thumb tip above or below the wrist by more than `THUMB_VERTICAL_MARGIN`.
4. The last `HISTORY_SIZE` (12) predictions are kept and a sign is shown only when at least `MAJORITY_RATIO` (60%) agree. After `NO_HAND_RESET_FRAMES` (20) frames with no sign, the display clears.

## Tuning (`config.py`)

| Setting | Effect |
|---|---|
| `EXTEND_ANGLE_THRESHOLD`, `THUMB_ANGLE_THRESHOLD` | Lower if extended fingers aren't detected, raise if bent fingers count as extended |
| `OK_PINCH_DISTANCE` | Raise if OK sign doesn't trigger, lower if it triggers too easily |
| `HISTORY_SIZE`, `MAJORITY_RATIO` | Higher = steadier but slower to change |
| `MODEL_COMPLEXITY` | 0 = fastest MediaPipe model |
| `MIN_DETECTION_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE` | Lower = more detections, shakier landmarks |

## Adding a sign

Add a new pattern to `classify_sign()` in `detection.py`, returning the label you want shown.
