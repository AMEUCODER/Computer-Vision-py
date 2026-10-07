"""
config.py
----------
All tunable constants for the sign identification app. Adjust values here
rather than digging through detection.py or main.py.
"""

# A finger's middle joint (PIP) angle is close to 180 deg when straight and
# drops sharply (toward 30-90 deg) when curled. This threshold decides the
# cutoff between "extended" and "curled".
#   - LOWER this if fully-extended fingers aren't being recognized as extended.
#   - RAISE this if slightly-bent fingers are being falsely called extended.
EXTEND_ANGLE_THRESHOLD = 160

# Same idea but for the thumb, which has a different joint structure and
# tends to never fully straighten to 180 deg even when "extended".
THUMB_ANGLE_THRESHOLD = 150

# How close (in normalized 0-1 coordinate space) the thumb tip and index
# tip must be to count as an "OK sign" pinch.
#   - RAISE this if OK sign isn't triggering even when pinched.
#   - LOWER this if it triggers too easily/accidentally.
OK_PINCH_DISTANCE = 0.06

# How far (in normalized y) the thumb tip must be above/below the wrist to
# count as "up" vs "down" rather than sideways, for the thumbs up/down check.
THUMB_VERTICAL_MARGIN = 0.05

# Smoothing: how many recent frames' predictions to keep, and what fraction
# of them must agree before we "lock in" a displayed sign. Prevents flicker
# between two similar-looking signs on a per-frame basis.
HISTORY_SIZE = 12
MAJORITY_RATIO = 0.6

# If no hand (or no recognized sign) has been seen for this many frames,
# clear the display back to "no sign" instead of holding onto a stale one.
NO_HAND_RESET_FRAMES = 20

# MediaPipe Hands settings
MAX_NUM_HANDS = 1
MODEL_COMPLEXITY = 0            # 0 = fastest model variant
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
BUFFER_SIZE = 1                 # reduces latency from internal camera buffering
