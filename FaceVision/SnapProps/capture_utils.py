# =========================================================
# CAPTURE_UTILS — standalone, drop into ANY opencv project.
# Doesn't know about config.py/detection.py/filters.py at all.
#
# HOW TO USE IT (only 2 lines needed in your program):
#   capture = CountdownCapture()          # once, before the loop
#   frame = capture.update(frame, key)    # once, inside the loop
# =========================================================

import cv2
import os
import time


class CountdownCapture:
    """Press 'c' -> waits 5s (showing a countdown on screen) -> saves the frame."""

    def __init__(self, folder="capture", countdown_seconds=5):
        self.folder = folder
        self.countdown_seconds = countdown_seconds
        self.start_time = None          # None = no countdown running right now
        os.makedirs(self.folder, exist_ok=True)   # create the folder if it's missing

    def update(self, frame, key):
        """Call this once per loop. Returns frame (with countdown text drawn on it if active)."""
        if key == ord('c') and self.start_time is None:
            self.start_time = time.time()  # 'c' pressed -> start timing

        if self.start_time is not None:
            remaining = self.countdown_seconds - (time.time() - self.start_time)
            seconds_left = max(0, int(remaining) + 1)

            cv2.putText(frame, str(seconds_left),
                        (frame.shape[1] // 2 - 20, frame.shape[0] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

            if remaining <= 0:
                filename = os.path.join(self.folder, f"photo_{int(time.time())}.png")
                cv2.imwrite(filename, frame)
                print(f"Saved {filename}")
                self.start_time = None  # reset so 'c' can be pressed again

        return frame