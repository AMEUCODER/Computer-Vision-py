"""
config.py
----------
All tunable constants for the Air Draw app. Adjust values here rather
than digging through detection.py, canvas.py, or main.py.
"""

# A finger's middle joint (PIP) angle is near 180 deg when straight, much
# less when curled. This is how we tell "finger up" from "finger down" -
# using the angle instead of a plain y-coordinate check means it still
# works no matter how your hand is rotated.
EXTEND_ANGLE_THRESHOLD = 160

# --- Drawing ---
DRAW_COLOR = (255, 0, 0)     # blue (OpenCV uses BGR, not RGB)
BRUSH_THICKNESS = 8
ERASER_THICKNESS = 50

# Smooths fingertip jitter: 0 = raw/jittery, closer to 1 = smoother but
# slightly laggier. Simple exponential moving average.
SMOOTHING = 0.5

# --- Camera ---
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# --- MediaPipe / performance ---
# Detect the hand on a smaller copy of the frame for speed. 0.5 = detect
# on a half-size copy. Lower = faster but worse at picking up a hand
# that's small/far from the camera. Raise toward 0.75 if detection feels
# unreliable and you have CPU headroom to spare.
DETECTION_SCALE = 0.5

MODEL_COMPLEXITY = 0            # 0 = fastest MediaPipe model variant
MAX_NUM_HANDS = 1

# LOWERING these makes MediaPipe more willing to report a detection it's
# less sure about - fewer dropped frames, but occasionally a
# shakier/less accurate landmark.
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.5

# If the hand isn't detected for this many consecutive frames or fewer,
# keep the line going instead of starting a new one - a single missed
# frame (common during fast movement or motion blur) shouldn't visibly
# break your drawing. Only a miss LONGER than this actually lifts the pen.
MISS_GRACE_FRAMES = 4
