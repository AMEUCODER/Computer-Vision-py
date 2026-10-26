# Computer Vision Playground

Real-time computer vision projects in Python: hand-gesture recognition, live camera filters, and camera-controlled games, built with OpenCV, MediaPipe, NumPy, Pygame and Tkinter. The focus is practical, real-time image processing that balances accuracy with speed.

## Projects

| Project | Category | What it does | Folder |
|---|---|---|---|
| **Hand Gesture Filter Camera** | HandVision | Switch live filters by holding up 0-5 fingers, hands-free photo countdown, video recording. | [`HandVision/HandVision-filters`](./HandVision/HandVision-filters) |
| **Air Draw** | HandVision | Draw in the air with your index finger; two-finger erase, fist to clear. | [`HandVision/Air-Draw`](./HandVision/Air-Draw) |
| **Rock-Paper-Scissors** | HandVision | Play against the computer using your real hand, with a countdown and scoreboard. | [`HandVision/Rock-papper-scissors`](./HandVision/Rock-papper-scissors) |
| **Sign Identification** | HandVision | Recognizes 10 hand signs (fist, peace, thumbs up, OK, ...) with rule-based geometry, no training data. | [`HandVision/Sign-Identification`](./HandVision/Sign-Identification) |
| **Head-Tilt Traffic Racer** | GameVision | Steer a car through 3-lane traffic by tilting your head. Difficulty modes and a top-5 leaderboard. | [`GameVision/FlappyBird`](./GameVision/FlappyBird) |

> `DocVision`, `RadarVision` and `GameVision/2D-Car-Game` are reserved folders for upcoming projects and contain no code yet.

## Tech Stack

| Library | Used for |
|---|---|
| **OpenCV** | Camera capture, image processing, filters, edge detection, Haar-cascade face detection |
| **MediaPipe** | Pretrained hand and face landmark tracking (21 hand points, 468 face points) |
| **NumPy** | Array math for filters, angles and distances |
| **Pygame** | Window, input and rendering for the camera-controlled game |

## Setup

Python 3.9-3.12 is recommended.

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Then open a project folder and follow its own README (usually `python main.py`).

### Important: MediaPipe version

These projects use the legacy `mp.solutions` API (`mp.solutions.hands`, `mp.solutions.face_mesh`), which was removed in newer MediaPipe releases. `requirements.txt` pins `mediapipe==0.10.21`, the last version that still ships it. If you see `AttributeError: module 'mediapipe' has no attribute 'solutions'`, you have a newer version installed:

```bash
pip install mediapipe==0.10.21
```

## Repository Structure

```
.
├── HandVision/
│   ├── HandVision-filters/      # finger-count filters, photo + video capture
│   ├── Air-Draw/                # draw in the air
│   ├── Rock-papper-scissors/    # RPS game vs. the computer
│   └── Sign-Identification/     # rule-based hand-sign classifier
├── FaceVision/
│   └── SnapProps/               # face-tracked AR props and filters
├── GameVision/
│   ├── 2D-Car-Game/             # Head-Tilt Traffic Racer (full version, all assets generated in code)
│   └── FlappyBird/              # earlier Head-Tilt Traffic Racer prototype (folder name is historical)
├── ImgVision/
│   └── outpainting/             # batch background outpainter with a desktop GUI
├── SafetyVision/
│   └── WatchDog/                # YOLOv4-tiny webcam security monitor with alarm + phone alerts
├── DocVision/                   # reserved
├── RadarVision/                 # reserved
├── requirements.txt
├── LICENSE
└── README.md
```

## Design Principles

- **Real-time first.** Detection runs on live video, so speed and responsiveness matter as much as precision.
- **Minimal dependencies.** Core CV libraries only.
- **Readable, commented code.** Each project is meant to be learned from, not just run. Tunable numbers live in a `config.py` per project.
- **Rule-based where possible.** Most gesture logic is geometry over landmarks (joint angles, distances), so there is no dataset to collect and no model to train.

## License

[MIT](./LICENSE)
