# WatchDog

A webcam security monitor built with OpenCV and a YOLOv4-tiny object detector.
It watches the live camera feed, flags people it sees with a bounding box,
sounds an alarm and sends a phone notification when a person is detected
with high confidence, and keeps a running count of people who have left
the frame.

## Features

- Real-time object detection (YOLOv4-tiny, all 80 COCO classes) on a live webcam feed
- Bounding boxes color-coded by confidence: red = high-confidence person, yellow = low-confidence person, grey = any other detected object
- Audio alarm (plays `police.mp3`) when a person is detected above the confidence threshold
- Phone push notifications via [ntfy.sh](https://ntfy.sh), rate-limited to one every 30 seconds so it doesn't spam you
- A simple position-based tracker that counts how many people have left the frame (shown on-screen as "People Left Frame")

## Files

| File | Purpose |
|---|---|
| `WatchDog.py` | Main program — run this |
| `yolov4-tiny.cfg` | YOLOv4-tiny network architecture (Darknet config format) |
| `yolov4-tiny.weights` | Pre-trained YOLOv4-tiny weights (~24 MB) |
| `coco.names` | The 80 class names the model can recognize, one per line, in the order the model outputs them |
| `police.mp3` | Alarm sound played when a person is detected |
| `info.md` | Development notes: known gaps and ideas for what to build next |

## Requirements

- Python 3.9+
- A working webcam
- These packages:
  ```
  pip install opencv-python requests playsound==1.2.2
  ```
  (Pin `playsound` to `1.2.2` — newer versions often fail silently on Windows.)
- `yolov4-tiny.cfg`, `yolov4-tiny.weights`, `coco.names`, and `police.mp3` must stay in the same folder as `WatchDog.py`
- Internet access is only needed for the phone notifications — detection and the alarm sound both work fully offline
- A phone with the [ntfy](https://ntfy.sh/) app, subscribed to your topic (see Configuration below)

## Configuration

Before running, open `WatchDog.py` and change this line:

```python
NTFY_TOPIC = "CHANGE-ME-random-topic-8472"
```

to your own private, hard-to-guess topic name, then subscribe to that same
topic name in the ntfy app on your phone. Anyone who knows your topic name
can read your alerts, so don't use something guessable like `my-alarm`.

If you have more than one camera, change `cv2.VideoCapture(0)` to `1` or `2`.

## Usage

```
python WatchDog.py
```

- A window opens showing the live camera feed with detection boxes drawn on it.
- Press `q` to quit.
- There is currently no way to arm/disarm or pause detection while the program is running (see Known Limitations).

## Known Limitations

This was built and syntax-checked, but not yet tested against a real camera
feed — expect to tune the thresholds below once you try it in your own room
and lighting.

- **The alarm has no cooldown of its own.** Only the `person` class can
  trigger it (that check is already in the code), but once it does, there's
  nothing stopping it from retriggering as soon as the previous play
  finishes if the same person is still standing in frame — only the ntfy
  phone notification is rate-limited (max one per 30 seconds), not the
  alarm sound itself.
- **Errors are hidden.** `play_alarm()` has a bare `except Exception: pass` —
  if the sound genuinely fails to play, you get silence and no error message
  at all, which makes debugging a "no sound" report hard.
- **The exit counter is approximate.** It matches each detected person to the
  nearest previously-tracked position. Two people who cross paths can swap
  IDs, and someone hidden behind furniture for more than 10 frames may get
  counted as having "left" even if they're still in the room. It also can't
  tell which direction someone left in — only that they were near the edge
  of the frame when their track was dropped.
- **Nothing is saved.** No snapshot, video clip, or log entry is produced
  when the alarm triggers — only the on-screen counter and the one-time
  phone push.
- **Lighting and distance matter a lot.** YOLOv4-tiny is fast but trades
  away accuracy on small or far-away objects compared to full YOLOv4.

## What to Add Next

Roughly easiest-to-hardest:

1. **Snapshot on alarm** — save the triggering frame (`cv2.imwrite(f"alerts/{int(time.time())}.jpg", frame)`) and attach it to the ntfy notification.
2. **Event log** — append timestamp, label, and confidence to a CSV file every time the alarm fires, so you have a history to review later.
3. **Arm/disarm key** — press a key (e.g. `a`) to toggle detection on/off without closing the program.
4. **Surface hidden errors** — replace `except Exception: pass` in `play_alarm()` with at least a `print(e)` while you're testing.
5. **Detection zone** — only alarm when a person is inside a rectangle you draw (e.g. a doorway), instead of anywhere in frame.
6. **Line-crossing counter with direction** — replace the edge-based "left the frame" trick with a virtual line that counts people crossing in vs. out.
7. **Better tracker** — for busier scenes, swap the current nearest-position tracker for something like ByteTrack (via the `supervision` library).
8. **Night mode / schedule** — only run detection during set hours.
9. **Telegram bot instead of ntfy** — richer notifications (photos, two-way commands like `/status`).
10. **Small dashboard** — a tkinter or web page showing the live feed, running counts, and alert history.

See `info.md` for more detail on each of these, plus a suggested next full
project (a shop footfall counter) that reuses this detection + tracking code.
