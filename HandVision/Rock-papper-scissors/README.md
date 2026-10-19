# Rock-Paper-Scissors (Live Camera Game)

Play Rock-Paper-Scissors against the computer using your real hand. Built with OpenCV and MediaPipe, using joint-angle geometry over hand landmarks instead of a trained model, so sign detection is fast and works at any hand rotation.

## How to play

1. Run the game and show your hand to the camera.
2. Press **Space** to start a round. A 3-second countdown runs.
3. On "SHOOT", make Rock, Paper or Scissors.
4. The computer picks a move, the result is shown, and the scoreboard updates.

| Sign | Hand shape |
|---|---|
| Rock | Closed fist |
| Paper | All five fingers extended |
| Scissors | Index and middle fingers extended, others curled |

## Controls

| Key | Action |
|---|---|
| `Space` | Start a round (when idle) |
| `r` | Reset the scoreboard |
| `q` | Quit |

## Setup

```bash
pip install opencv-python mediapipe==0.10.21 numpy
python main.py
```

`mediapipe==0.10.21` is required because this project uses the legacy `mp.solutions` API.

## Project structure

```
Rock-papper-scissors/
├── main.py        # game loop, state machine, scoreboard, webcam feed
├── signID.py      # joint-angle math, finger states, Rock/Paper/Scissors rules, winner logic
├── interface.py   # on-screen UI and move icons
├── config.py      # thresholds, timings, game states
└── README.md
```

## How it works

- **Finger state:** for each finger the angle at the middle joint is computed (`calc_angle`). Above `EXTEND_ANGLE_THRESHOLD` (160 degrees) the finger counts as extended. The thumb has its own threshold (150 degrees).
- **Classification:** the five extended/curled flags are matched against fixed patterns in `classify_rps`. Anything that doesn't match is ignored.
- **Smoothing:** the last `HISTORY_SIZE` (10) predictions are kept and a sign is only accepted when at least `MAJORITY_RATIO` (60%) agree, so single noisy frames don't change your move.
- **State machine:** `IDLE -> COUNTDOWN -> SHOOT -> RESULT -> IDLE`. Timings (countdown, flash, result display, capture grace period) are in `config.py`.

## Tuning

If your sign isn't recognized, lower `EXTEND_ANGLE_THRESHOLD` or `THUMB_ANGLE_THRESHOLD`. If bent fingers count as extended, raise them. Raise `HISTORY_SIZE` for steadier reads at the cost of a little delay.
