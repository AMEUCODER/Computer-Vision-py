# SentryCam: info, gaps and ideas

## 1. Things needed to run it
- Python 3.9+ and a working webcam (`VideoCapture(0)`; try 1 or 2 if you have several cameras)
- `pip install opencv-python requests playsound==1.2.2` (newer playsound versions often fail on Windows; if sound is silent, this is the first thing to try)
- `yolov4-tiny.cfg`, `yolov4-tiny.weights`, `coco.names` and `police.mp3` in the same folder as the script
- Internet connection for phone notifications only (detection and alarm work offline)
- A phone with the ntfy app subscribed to your topic

## 2. Missing information / known gaps
- **Any non-person object triggers the alarm.** A chair, bottle, laptop, backpack or TV counts as "not a person". In a normal room this will false-alarm constantly. Fix: only alarm on a list of classes, for example `ALERT = {"dog", "cat", "car", "backpack"}` and check `label in ALERT`.
- **Errors are hidden.** `play_alarm` has `except Exception: pass`, so if the sound fails you get silence and no message. Replace `pass` with `print(e)` while testing.
- **The exit counter is basic.** It matches people to their last position. People who cross paths can swap identities, and a person hidden behind an object for more than 10 frames may be counted twice. It also has no idea which direction they left, only that they were near an edge.
- **Nothing is saved.** No log, no photos, no video clip when the alarm triggers.
- **The alarm never stops by itself.** It plays the full mp3 each time and replays while the object is still there.
- **The ntfy topic is the only protection.** Anyone who guesses the name can read your alerts. Use a long random topic, or a self-hosted/authenticated ntfy later.
- **Not tested on real hardware by me.** I only checked the syntax and the exit counter on simulated data, so expect to adjust thresholds with your camera.
- yolov4-tiny is fast but misses small or far away objects. Lighting matters a lot.

## 3. Things you can add (easiest first)
1. **Class whitelist** for the alarm (see gap 1).
2. **Snapshot on alarm**: `cv2.imwrite(f"alerts/{int(time.time())}.jpg", frame)`, and send it to your phone with ntfy's attachment header.
3. **Event log**: append time, label and confidence to a CSV file.
4. **Arm/disarm keys**: press `a` to toggle the alarm on and off.
5. **Detection zone**: only alarm when something is inside a rectangle you draw (a door, a shelf).
6. **Line-crossing counter**: count people going *in* and *out* across a line, with direction, instead of the edge trick.
7. **Better tracker**: swap my tracker for ByteTrack (the `supervision` library) for crowds.
8. **Night mode / schedule**: only active at set hours.
9. **Telegram bot** instead of ntfy, to send photos and take commands like `/status`.
10. **Small tkinter or web dashboard** showing the live feed, counts and alert history.

## 4. What to build next
**Shop footfall counter (recommended).** Reuse this project: people detection, tracking and the counter already exist. Add a virtual line at the door that counts people in and out with direction, log it to a CSV with timestamps, and produce a daily summary (visitors per hour, busiest time, current occupancy). Why this one:
- It is a real problem local shops pay attention to (how many people come in versus how many buy).
- It fits your freelancing plan: easy to demo on a laptop with a webcam, and the output (a clean daily report) is something a shop owner understands.
- It teaches the one skill this project is missing: robust tracking and line crossing.

Other good options:
- **Hand gesture control** project from earlier, extended to control the alarm (open palm to disarm).
- **Face filter app** polished into a small product for Instagram brands.
- **Smart attendance** using face recognition, for small classes or gyms.

Suggested order: finish SentryCam (whitelist, snapshot, log), then build the footfall counter on top of it.
