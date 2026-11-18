"""
capture.py
-----------
Adds two extra features on top of the gesture-filter loop:

  1. HOLD UP ONE FINGER for HOLD_TRIGGER_SECONDS seconds straight
     -> starts a Pixel-camera-style COUNTDOWN_SECONDS countdown overlay
     -> then automatically saves a photo when it reaches 0.

  2. Press 'f' at any time to START/STOP recording the live (filtered)
     feed to an .mp4 video file. Press 'f' again to stop.

Both behaviors are wrapped in the GestureCapture class - main.py just
creates one instance and calls its methods once per frame.
"""

import cv2
import time
import os

PHOTO_OUTPUT_DIR = "captures/photos"
VIDEO_OUTPUT_DIR = "captures/videos"

TRIGGER_FINGER_COUNT = 1        # which finger count starts the hold timer
HOLD_TRIGGER_SECONDS = 5        # how long that gesture must be held before the countdown starts
COUNTDOWN_SECONDS = 5           # length of the on-screen countdown before the photo is taken
GRACE_SECONDS = 0.4             # tolerate brief misreads of the gesture without resetting the hold timer

VIDEO_FPS = 20.0                # assumed frame rate for the saved video file


class GestureCapture:
    def __init__(self):
        os.makedirs(PHOTO_OUTPUT_DIR, exist_ok=True)
        os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

        # --- hold-to-trigger photo state ---
        self._hold_start_time = None        # when the "1 finger" gesture was first seen
        self._last_trigger_seen_time = None  # last frame the gesture was actually read as 1
        self._countdown_start_time = None    # when the visible countdown itself began

        # --- video recording state ---
        self._video_writer = None
        self._recording = False

    # -----------------------------------------------------------------
    # PHOTO: hold one finger -> countdown -> auto capture
    # -----------------------------------------------------------------
    def update_photo_trigger(self, frame, finger_count):
        """
        Call every frame with the current finger_count (0-5 or None).
        Returns the frame with a hold-progress bar or countdown drawn on
        it when relevant. Saves a photo automatically once the countdown
        finishes.
        """
        now = time.time()

        if self._countdown_start_time is not None:
            # A countdown is already running - let it finish regardless of
            # whether the hand is still visible, just like a phone timer.
            elapsed = now - self._countdown_start_time
            remaining = COUNTDOWN_SECONDS - elapsed

            if remaining <= 0:
                self._capture_photo(frame)
                self._countdown_start_time = None
                self._hold_start_time = None
            else:
                self._draw_countdown(frame, remaining)

            return frame

        # No countdown yet - check whether the trigger gesture is being held.
        if finger_count == TRIGGER_FINGER_COUNT:
            if self._hold_start_time is None:
                self._hold_start_time = now
            self._last_trigger_seen_time = now

            held_for = now - self._hold_start_time
            if held_for >= HOLD_TRIGGER_SECONDS:
                self._countdown_start_time = now
            else:
                self._draw_hold_progress(frame, held_for)

        elif self._hold_start_time is not None:
            # Gesture dropped - but tolerate a brief misread (GRACE_SECONDS)
            # before actually resetting the hold timer, since a single
            # noisy frame shouldn't throw away several seconds of holding.
            if now - self._last_trigger_seen_time > GRACE_SECONDS:
                self._hold_start_time = None
            else:
                held_for = now - self._hold_start_time
                self._draw_hold_progress(frame, held_for)

        return frame

    def _capture_photo(self, frame):
        filename = os.path.join(PHOTO_OUTPUT_DIR, f"photo_{int(time.time())}.png")
        cv2.imwrite(filename, frame)
        print(f"Photo captured: {filename}")

    def _draw_hold_progress(self, frame, held_for):
        # Small progress bar showing how close the hold is to triggering.
        progress = min(held_for / HOLD_TRIGGER_SECONDS, 1.0)

        bar_x, bar_y, bar_w, bar_h = 10, 50, 200, 12
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), 1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + bar_h), (0, 255, 255), -1)
        cv2.putText(frame, "Hold 1 finger to start timer", (bar_x, bar_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    def _draw_countdown(self, frame, remaining):
        # Pixel-camera style: dim circle, big number, shrinking ring.
        h, w = frame.shape[:2]
        center = (w // 2, h // 2)

        seconds_left = int(remaining) + 1          # show 5,4,3,2,1 rather than 4,3,2,1,0
        frac_this_second = remaining - int(remaining)  # animates the ring within each second

        # Dim overlay behind the number so it stands out over any filter.
        overlay = frame.copy()
        cv2.circle(overlay, center, 90, (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Shrinking ring that empties out over the course of each second.
        ring_radius = 80
        angle = int(360 * frac_this_second)
        cv2.ellipse(frame, center, (ring_radius, ring_radius), -90, 0, angle, (0, 255, 255), 6)

        # Big countdown number in the center.
        text = str(seconds_left)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 3.0
        thickness = 6
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_pos = (center[0] - text_w // 2, center[1] + text_h // 2)
        cv2.putText(frame, text, text_pos, font, font_scale, (255, 255, 255), thickness)

    # -----------------------------------------------------------------
    # VIDEO: press 'f' to start/stop recording
    # -----------------------------------------------------------------
    def handle_key(self, key, frame_shape):
        """Call this every frame with the cv2.waitKey() result."""
        if key == ord('f'):
            if self._recording:
                self._stop_recording()
            else:
                self._start_recording(frame_shape)

    def _start_recording(self, frame_shape):
        h, w = frame_shape[:2]
        filename = os.path.join(VIDEO_OUTPUT_DIR, f"video_{int(time.time())}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._video_writer = cv2.VideoWriter(filename, fourcc, VIDEO_FPS, (w, h))
        self._recording = True
        print(f"Recording started: {filename}")

    def _stop_recording(self):
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None
        self._recording = False
        print("Recording stopped.")

    def write_video_frame(self, frame):
        """Call every frame - no-op if not currently recording."""
        if self._recording and self._video_writer is not None:
            self._video_writer.write(frame)

    def draw_recording_indicator(self, frame):
        """Call every frame to draw a red REC dot while recording."""
        if self._recording:
            cv2.circle(frame, (30, frame.shape[0] - 30), 8, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (45, frame.shape[0] - 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return frame

    def release(self):
        """Call on shutdown so any open video file gets finalized properly."""
        self._stop_recording()
