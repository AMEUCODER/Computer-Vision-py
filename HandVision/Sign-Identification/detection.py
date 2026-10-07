"""
detection.py
--------------
MediaPipe hand tracking + geometric feature extraction + rule-based sign
classification. This is "Path A" from the gesture-recognition roadmap: no
training data, just geometric rules over MediaPipe's 21 hand landmarks.

Key upgrade over simple finger-counting: instead of comparing a fingertip's
y-coordinate to its knuckle's y-coordinate (which only works when the hand
is upright), this measures the actual bend ANGLE at each finger's middle
joint. That makes it rotation-invariant - a peace sign held sideways still
gets recognized correctly, not just one held upright.

Recognized signs (starter vocabulary - see classify_sign() to add more):
  Fist, Open Palm, Thumbs Up, Thumbs Down, Peace/Victory, Pointing,
  Rock On, Call Me, I Love You (ASL), OK Sign
"""

import numpy as np
import mediapipe as mp

import config

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def create_hand_detector():
    """Builds a configured MediaPipe Hands instance, ready to use in a `with` block."""
    return mp_hands.Hands(
        max_num_hands=config.MAX_NUM_HANDS,
        model_complexity=config.MODEL_COMPLEXITY,
        min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
    )


def draw_hand_landmarks(frame, hand_landmarks):
    """Draws the hand skeleton overlay onto the frame in place."""
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
        mp_styles.get_default_hand_landmarks_style(),
        mp_styles.get_default_hand_connections_style(),
    )


# ---------------------------------------------------------------------------
# FEATURE EXTRACTION: joint angles, not raw coordinates
# ---------------------------------------------------------------------------

def calc_angle(a, b, c):
    """
    Angle (in degrees) at point b, formed by the two segments a-b and c-b.
    Each point is an (x, y) tuple. This is the core geometric building
    block: straight finger = ~180 deg at the middle joint, curled = much
    less.
    """
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    # +1e-6 avoids a divide-by-zero if two landmarks land on the same pixel
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)  # guard against float rounding
    return np.degrees(np.arccos(cos_angle))


def lm_xy(landmarks, idx):
    """Pull just the (x, y) of one landmark - MediaPipe also gives z, unused here."""
    return (landmarks[idx].x, landmarks[idx].y)


def get_finger_states(landmarks):
    """
    Returns {finger_name: bool} - whether each finger is extended, based on
    the bend angle at its middle joint rather than a simple coordinate
    comparison. This is what makes detection work at any hand rotation.
    """
    states = {}

    # For index/middle/ring/pinky: measure the angle AT the PIP joint,
    # between the vectors pointing toward the MCP (knuckle) and the TIP.
    finger_joints = {
        "index":  (5, 6, 8),
        "middle": (9, 10, 12),
        "ring":   (13, 14, 16),
        "pinky":  (17, 18, 20),
    }
    for name, (mcp, pip, tip) in finger_joints.items():
        angle = calc_angle(lm_xy(landmarks, mcp), lm_xy(landmarks, pip), lm_xy(landmarks, tip))
        states[name] = angle > config.EXTEND_ANGLE_THRESHOLD

    # Thumb: same idea, but using its own joint chain (CMC -> MCP -> TIP),
    # since the thumb only has 2 real joints instead of 3.
    thumb_angle = calc_angle(lm_xy(landmarks, 1), lm_xy(landmarks, 2), lm_xy(landmarks, 4))
    states["thumb"] = thumb_angle > config.THUMB_ANGLE_THRESHOLD

    return states


# ---------------------------------------------------------------------------
# RULE ENGINE: finger states -> named sign
# ---------------------------------------------------------------------------

def classify_sign(landmarks, states):
    """
    Maps the current finger states (+ a couple of extra position checks)
    to a human-readable sign name, or None if nothing matches.
    Add new signs here by adding new pattern checks.
    """
    thumb, index, middle, ring, pinky = (
        states["thumb"], states["index"], states["middle"], states["ring"], states["pinky"]
    )

    # OK sign is a special case: it's not about which fingers are extended,
    # it's about the thumb and index tip touching (a "pinch"), with the
    # other three fingers extended.
    thumb_tip = np.array(lm_xy(landmarks, 4))
    index_tip = np.array(lm_xy(landmarks, 8))
    pinch_distance = np.linalg.norm(thumb_tip - index_tip)
    if pinch_distance < config.OK_PINCH_DISTANCE and middle and ring and pinky:
        return "OK Sign"

    pattern = (thumb, index, middle, ring, pinky)

    # Straightforward patterns: exact combination of which fingers are up.
    if pattern == (False, False, False, False, False):
        return "Fist"
    if pattern == (True, True, True, True, True):
        return "Open Palm"
    if pattern == (False, True, True, False, False):
        return "Peace / Victory"
    if pattern == (False, True, False, False, False):
        return "Pointing"
    if pattern == (False, True, False, False, True):
        return "Rock On"
    if pattern == (True, False, False, False, True):
        return "Call Me"
    if pattern == (True, True, False, False, True):
        return "I Love You (ASL)"

    # Thumb-only pattern needs a direction check (up vs down) using the
    # thumb tip's position relative to the wrist, since "thumb extended"
    # alone doesn't tell you which way it's pointing.
    if pattern == (True, False, False, False, False):
        wrist_y = landmarks[0].y
        thumb_tip_y = landmarks[4].y
        if thumb_tip_y < wrist_y - config.THUMB_VERTICAL_MARGIN:
            return "Thumbs Up"
        elif thumb_tip_y > wrist_y + config.THUMB_VERTICAL_MARGIN:
            return "Thumbs Down"
        else:
            return "Thumb Out"

    return None  # doesn't match any known sign


def detect_sign(hands_detector, rgb_frame):
    """
    Runs MediaPipe on one RGB frame and returns (sign_name_or_None,
    hand_landmarks_or_None). hand_landmarks is returned so the caller can
    draw it, without detection.py needing to know about cv2 drawing calls.
    """
    rgb_frame.flags.writeable = False
    results = hands_detector.process(rgb_frame)
    rgb_frame.flags.writeable = True

    if not results.multi_hand_landmarks:
        return None, None

    hand_landmarks = results.multi_hand_landmarks[0]
    landmarks = hand_landmarks.landmark

    states = get_finger_states(landmarks)
    sign = classify_sign(landmarks, states)

    return sign, hand_landmarks
