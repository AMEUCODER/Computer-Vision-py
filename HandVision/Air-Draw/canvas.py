"""
canvas.py
----------
The persistent drawing surface: line-drawing, erasing, clearing,
fingertip smoothing, the "grace period" that tolerates brief detection
misses, and blending the canvas onto the live camera frame.

Keeping all of this state in one class means main.py doesn't need to
juggle a handful of loose variables (canvas array, prev_point,
smoothed_point, frames_since_hand) itself.
"""

import cv2
import numpy as np

import config


class DrawingCanvas:
    def __init__(self):
        self._canvas = None          # created once we know the real frame size
        self._prev_point = None      # last fingertip position while drawing/erasing
        self._smoothed_point = None  # jitter-reduced fingertip position
        self._frames_since_hand = 0  # consecutive frames with no hand detected

    def _ensure_canvas(self, height, width):
        if self._canvas is None:
            self._canvas = np.zeros((height, width, 3), dtype=np.uint8)

    def _smooth(self, point):
        """Exponential moving average - reduces jitter in the drawn line."""
        if self._smoothed_point is None:
            self._smoothed_point = point
        else:
            self._smoothed_point = (
                int(config.SMOOTHING * self._smoothed_point[0] + (1 - config.SMOOTHING) * point[0]),
                int(config.SMOOTHING * self._smoothed_point[1] + (1 - config.SMOOTHING) * point[1]),
            )
        return self._smoothed_point

    def update(self, frame_shape, mode, fingertip):
        """
        Call this every frame with the current mode ("draw"/"erase"/
        "clear"/"idle") and fingertip pixel position when a hand was
        detected, or mode=None when no hand was found this frame.
        """
        height, width = frame_shape[:2]
        self._ensure_canvas(height, width)

        if mode is None:
            # Don't immediately break the line on a single missed frame -
            # only lift the pen once misses have gone on for longer than
            # MISS_GRACE_FRAMES in a row.
            self._frames_since_hand += 1
            if self._frames_since_hand > config.MISS_GRACE_FRAMES:
                self._prev_point = None
                self._smoothed_point = None
                return "idle (lost hand)"
            return "idle"

        self._frames_since_hand = 0
        point = self._smooth(fingertip)

        if mode == "draw":
            if self._prev_point is None:
                self._prev_point = point  # start fresh, no stray line
            cv2.line(self._canvas, self._prev_point, point, config.DRAW_COLOR, config.BRUSH_THICKNESS)
            self._prev_point = point

        elif mode == "erase":
            if self._prev_point is None:
                self._prev_point = point
            cv2.line(self._canvas, self._prev_point, point, (0, 0, 0), config.ERASER_THICKNESS)
            self._prev_point = point

        elif mode == "clear":
            self._canvas[:] = 0
            self._prev_point = None

        else:  # idle
            self._prev_point = None

        return mode

    def blend_onto(self, frame):
        """
        Returns `frame` with the canvas drawn on top. Wherever the canvas
        has real drawing (non-black), the canvas shows through; everywhere
        else, the live camera feed shows through. Keeps drawings solid and
        stable as the background changes.
        """
        self._ensure_canvas(*frame.shape[:2])

        canvas_gray = cv2.cvtColor(self._canvas, cv2.COLOR_BGR2GRAY)
        _, inv_mask = cv2.threshold(canvas_gray, 20, 255, cv2.THRESH_BINARY_INV)
        inv_mask_3ch = cv2.cvtColor(inv_mask, cv2.COLOR_GRAY2BGR)

        frame_bg = cv2.bitwise_and(frame, inv_mask_3ch)
        return cv2.bitwise_or(frame_bg, self._canvas)
