# Head-Tilt Traffic Racer

A 3-lane traffic-dodging game controlled by tilting your head in front of a webcam. No keyboard or mouse needed to steer.

> The folder is still named `FlappyBird` from an earlier version of the project. The game in it is the Traffic Racer described here.

## Screenshots

<table>
  <tr>
    <td align="center">
      <img src="screenshot1.png" width="220" alt="Gameplay view"/>
      <br />
      <sub><b>Gameplay / crash screen</b></sub>
    </td>
    <td align="center">
      <img src="screenshot2.png" width="220" alt="Leaderboard view"/>
      <br />
      <sub><b>Top scores leaderboard</b></sub>
    </td>
  </tr>
</table>

## Setup

```bash
pip install opencv-python mediapipe==0.10.21 pygame numpy
python main.py
```

`mediapipe==0.10.21` is required because this project uses the legacy `mp.solutions.face_mesh` API, which newer MediaPipe releases removed.

## Controls

- **Tilt your head** left or right to steer the car.
- **Mouse:** click START, SCORES, BACK, RETRY, MENU, and the top-bar SOUND and MODE buttons.
- **Keyboard:** type your name when you reach the top 5 and confirm with Enter.

## What it uses

| Piece | Library | Why |
|---|---|---|
| Camera capture | `opencv-python` | Reads and mirrors webcam frames |
| Face landmarks | `mediapipe` FaceMesh | 468 landmarks per frame from a pretrained model |
| Window, input, rendering | `pygame` | Event loop, drawing, fonts, timing |
| Glue and audio | `numpy` | Converts frames to a pygame surface and synthesizes the engine sound |
| Leaderboard | `json` | Stores `traffic_scores.json` next to the script |

No model is trained: MediaPipe does the perception and the "gesture" is one `atan2` call.

## Project structure

| File | Responsibility |
|---|---|
| `main.py` | Entry point: game loop, state machine, traffic cars |
| `interface.py` | `HeadTracker` (camera thread), `Button`, road and car drawing |
| `config.py` | Window size, lanes, colors, difficulty presets, engine sound synthesis |
| `score.py` | `HighScores`: JSON-backed top-5 leaderboard |

All files must stay in the same folder because they import each other by module name.

## How it works

1. **Head tracking on its own thread.** `HeadTracker` reads frames, mirrors them, converts BGR to RGB, and runs FaceMesh in the background so face detection never stalls the game loop. The game reads the latest tilt each frame under a lock.
2. **Tilt angle.** The angle of the line between two outer eye-corner landmarks is computed with `math.atan2(dy, dx)`. It is near zero when your head is level and swings positive or negative as you tilt.
3. **Calibration.** Pressing START or RETRY stores your current tilt as `neutral`. The game then uses `tilt - neutral`, so it adapts to your seating position and camera angle.
4. **Steering.** The calibrated tilt is clamped to +/-0.5, scaled into a target x-position, and the car eases toward it smoothly (it is not locked to lanes).
5. **Traffic and collisions.** NPC cars spawn in random lanes at the difficulty's spawn rate, move relative to road speed, and a rectangle overlap with the player ends the run.
6. **State machine.** The game moves between `menu`, `playing`, `dead`, `name_entry` and `scores`, with every transition setting a literal state.
7. **Difficulty (`MODE` button).**

   | Mode | Road speed | Spawn interval (s) | NPC speed |
   |---|---|---|---|
   | EASY | 250 | 1.5 | 100 |
   | MEDIUM | 380 | 1.1 | 150 |
   | HARD | 520 | 0.7 | 200 |

8. **Generated sound.** `create_engine_loop()` synthesizes a retro engine hum (saw wave plus noise) with NumPy and plays it through `pygame.sndarray`. There are no audio files. The **SOUND** button toggles it.
9. **Leaderboard.** Scores load from `traffic_scores.json`, sorted and capped at 5. If a run beats 5th place you are routed to the name-entry screen, and saving writes the file immediately.

## Troubleshooting

- **`module 'mediapipe' has no attribute 'solutions'`:** install `mediapipe==0.10.21`.
- **Car drifts or steers wrongly:** sit level and press RETRY to recalibrate.
- **No camera:** close other apps using the webcam, or change the camera index passed to `HeadTracker`.
