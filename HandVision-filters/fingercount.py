"""
fingercount.py
----------------
MediaPipe hand landmark tracking + finger-extended counting logic.

Import from this file:
  - hands, mp_hands, mp_drawing  (needed by main.py to process frames and draw)
  - count_fingers(hand_landmarks, handedness_label) -> int (0-5)
"""

import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,                # 1 hand keeps finger-counting unambiguous;
                                     # raise to 2 if you want per-hand counts
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ---------------------------------------------------------------------------
# LANDMARK INDEX REFERENCE (mediapipe hand model - fixed, always the same)
# ---------------------------------------------------------------------------
# Each hand has 21 landmarks (0-20). The ones we need:
#   4  = thumb tip        3  = thumb IP joint  (joint just below the tip)
#   8  = index tip        6  = index PIP joint
#   12 = middle tip        10 = middle PIP joint
#   16 = ring tip           14 = ring PIP joint
#   20 = pinky tip          18 = pinky PIP joint
#
# "Extended" logic:
#   - For 4 fingers (index/middle/ring/pinky): a finger counts as UP if its
#     TIP is higher on screen (smaller y-value) than its PIP joint below it.
#     Because image y-coordinates increase DOWNWARD, "higher on screen" = smaller y.
#   - For the thumb: it moves sideways rather than up/down, so we compare
#     x-coordinates instead of y.

FINGER_TIPS = [8, 12, 16, 20]     # tip landmark IDs for index, middle, ring, pinky
FINGER_PIPS = [6, 10, 14, 18]     # corresponding joint just below each tip

THUMB_TIP = 4
THUMB_IP = 3


def count_fingers(hand_landmarks, handedness_label):
    """
    Returns an integer 0-5: how many fingers are extended on this hand.
    handedness_label is 'Left' or 'Right' as reported by mediapipe -
    needed because thumb direction flips depending on which hand it is.
    """
    landmarks = hand_landmarks.landmark
    fingers_up = 0

    # --- Thumb: compare x-coordinates (sideways motion) ---
    # NOTE: mediapipe's 'Left'/'Right' label refers to the hand as seen from
    # the camera's perspective, but since we cv2.flip() the frame for a
    # mirror view, the labels end up matching what YOU see in the mirror.
    if handedness_label == "Right":
        thumb_up = landmarks[THUMB_TIP].x < landmarks[THUMB_IP].x
    else:
        thumb_up = landmarks[THUMB_TIP].x > landmarks[THUMB_IP].x

    if thumb_up:
        fingers_up += 1

    # --- Other 4 fingers: compare y-coordinates (up/down motion) ---
    for tip_id, pip_id in zip(FINGER_TIPS, FINGER_PIPS):
        if landmarks[tip_id].y < landmarks[pip_id].y:   # tip above joint = finger extended
            fingers_up += 1

    return fingers_up
