# Air Draw

Draw in the air using your index finger, tracked live via MediaPipe and
rendered with OpenCV - no mouse, no stylus, no touchscreen.

## Screenshots

> Replace these with your own captures once you've run the app - I can't
> generate real screenshots of your webcam feed, but here's where they go:

| Draw mode | Erase mode | Cleared canvas |
|-----------|------------|----------------|
| ![Draw mode](screenshots/draw_mode.png) | ![Erase mode](screenshots/erase_mode.png) | ![Clear](screenshots/clear_mode.png) |

To capture one: run the app, press your OS's screenshot shortcut
(`Win+Shift+S` on Windows, `Cmd+Shift+4` on Mac) while a gesture is
active, and save it into a `screenshots/` folder next to this README.

## Setup

```
pip install opencv-python mediapipe numpy
python main.py
```

## Gestures

| Gesture | Action |
|---------|--------|
| Only index finger up | Draw |
| Index + middle finger up | Erase |
| Closed fist | Clear the whole canvas |

## Project Structure

```
air_draw_project/
├── main.py         # camera loop - run this
├── detection.py     # MediaPipe hand tracking + gesture classification
├── canvas.py         # the persistent drawing surface + blending
├── config.py         # every tunable number
└── README.md
```

## How It Works

1. MediaPipe tracks 21 hand landmarks per frame.
2. The angle at each finger's middle joint decides "up" vs "curled"
   (rotation-invariant - works at any hand angle).
3. Which fingers are up selects a mode: draw, erase, or clear.
4. The index fingertip's position is smoothed (exponential moving
   average) and used to draw a line on a persistent canvas image, which
   is blended on top of the live camera feed every frame.

---

## What's Next: Gesture-Controlled Volume & Mouse

Two natural follow-up projects use the exact same building blocks
(landmark tracking + geometric rules) you already have here, aimed at a
different output: instead of drawing pixels, they control something on
your OS.

### Gesture-Controlled Volume

**The core idea:** measure the distance between your thumb tip and index
tip (a "pinch"), and map that distance directly to a volume level.

1. **Track two points, not one.** Get the (x, y) of the thumb tip
   (landmark 4) and index tip (landmark 8) every frame - you're already
   doing this for the OK-sign detection in your sign identifier.
2. **Measure the pinch distance.** `distance = sqrt((x1-x2)^2 + (y1-y2)^2)`
   - pinched fingers together = small distance, spread apart = large
   distance.
3. **Calibrate the range.** Figure out roughly what distance means "fully
   pinched" (volume = 0) and what distance means "fully spread" (volume =
   100). This varies by hand size and camera distance, so either
   hard-code rough values or calibrate like the emotion tracker did
   (press a key with your hand at each extreme to record it).
4. **Map distance -> volume.** Use linear interpolation (`numpy.interp`)
   to convert the measured distance into a 0-100 volume value.
5. **Actually change the system volume.** This is the one genuinely new
   piece - you need a library that can talk to your OS's audio system:
   - **Windows:** `pycaw` (Python Core Audio Windows Library) lets you
     get/set the master volume directly.
   - **macOS:** you can shell out to
     `osascript -e "set volume output volume X"`.
   - **Linux:** `amixer` via a subprocess call, or `pulsectl` for
     PulseAudio.
6. **Give visual feedback.** Draw a vertical volume bar on screen (same
   `cv2.rectangle` technique as any progress bar) so you can see the
   current level without looking away from the camera window.

The whole thing is: two tracked points -> one distance measurement -> one
linear mapping -> one OS API call. No new detection concepts needed.

### Gesture-Controlled Mouse

**The core idea:** map your index fingertip's position directly onto
your screen's coordinate space, and move the OS cursor there every
frame. Use a second gesture (usually a pinch) to trigger a click.

1. **Get the fingertip position, normalized.** MediaPipe already gives
   you landmark positions as 0.0-1.0 fractions of the camera frame - you
   don't need pixel coordinates here, the fractions are exactly what you
   want.
2. **Get your actual screen size.** A library like `pyautogui` can tell
   you your monitor's resolution: `pyautogui.size()` returns
   `(screen_width, screen_height)`.
3. **Map fraction -> screen pixel.**
   `screen_x = fraction_x * screen_width`,
   `screen_y = fraction_y * screen_height`. Move the cursor there:
   `pyautogui.moveTo(screen_x, screen_y)`.
4. **Define an "active region" smaller than the full camera frame.**
   Using the ENTIRE camera frame means you'd have to move your hand to
   the physical edge of the camera's view to reach the screen edge,
   which is awkward. Instead, map only a smaller box in the middle of
   the frame (e.g. the middle 60%) to the full screen, so smaller hand
   movements cover the whole screen.
5. **Smooth the movement.** Raw fingertip tracking is jittery -
   translated directly to mouse movement, this looks like a shaky
   cursor. Use the exact same exponential-moving-average smoothing this
   project already uses for drawing.
6. **Add a click gesture.** A common choice: thumb+index pinch (same
   distance measurement as the volume idea above) below a threshold =
   `pyautogui.click()`. A different finger combination could trigger
   right-click or drag.

The whole thing is: one tracked point -> normalized coordinate mapping ->
smoothing -> one library call to move the cursor, plus a second gesture
reusing the same pinch-distance idea from volume control for clicking.

**Common pitfall for both:** `pyautogui`/`pycaw` calls can fight with
your own OpenCV window if you're not careful (e.g. moving the mouse
while trying to also read keyboard input for `cv2.waitKey`) - test these
in a simple standalone script before merging into a bigger app.
