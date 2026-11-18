"""
detection.py
--------------
MediaPipe hand tracking + angle-based finger-state detection + gesture
mode classification (draw / erase / clear / idle).
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
        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
        mp_styles.get_default_hand_landmarks_style(),
        mp_styles.get_default_hand_connections_style(),
    )


# ---------------------------------------------------------------------------
# FINGER STATE DETECTION
# ---------------------------------------------------------------------------

def calc_angle(a, b, c):
    """Angle in degrees at point b, formed by segments a-b and c-b."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))


def is_finger_up(landmarks, mcp, pip, tip):
    """True if the joint at `pip` is nearly straight (finger extended)."""
    a = (landmarks[mcp].x, landmarks[mcp].y)
    b = (landmarks[pip].x, landmarks[pip].y)
    c = (landmarks[tip].x, landmarks[tip].y)
    return calc_angle(a, b, c) > config.EXTEND_ANGLE_THRESHOLD


def get_hand_mode(landmarks):
    """
    Looks at which fingers are up and returns one of: "draw", "erase",
    "clear", or "idle" (anything else, e.g. hand mid-transition).
    """
    index_up = is_finger_up(landmarks, 5, 6, 8)
    middle_up = is_finger_up(landmarks, 9, 10, 12)
    ring_up = is_finger_up(landmarks, 13, 14, 16)
    pinky_up = is_finger_up(landmarks, 17, 18, 20)

    if index_up and middle_up and not ring_up and not pinky_up:
        return "erase"
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "draw"
    if not index_up and not middle_up and not ring_up and not pinky_up:
        return "clear"
    return "idle"


def fingertip_pixel(landmarks, width, height):
    """Index fingertip (landmark 8) position, converted to real pixel coordinates."""
    return (int(landmarks[8].x * width), int(landmarks[8].y * height))


def detect_hand(hands_detector, frame):
    """
    Runs MediaPipe on a downscaled copy of `frame` (for speed), then
    returns (mode, fingertip_px, hand_landmarks) using the FULL-SIZE
    frame's pixel coordinates - or (None, None, None) if no hand was found.

    MediaPipe's landmarks are normalized (0.0-1.0 fractions), so detecting
    on a smaller copy and applying the result to the full-size frame costs
    no accuracy, just less compute.
    """
    import cv2  # local import keeps this module's only cv2 dependency contained here

    height, width = frame.shape[:2]
    small = cv2.resize(frame, None, fx=config.DETECTION_SCALE, fy=config.DETECTION_SCALE)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb)

    if not results.multi_hand_landmarks:
        return None, None, None

    hand_landmarks = results.multi_hand_landmarks[0]
    landmarks = hand_landmarks.landmark

    mode = get_hand_mode(landmarks)
    fingertip = fingertip_pixel(landmarks, width, height)

    return mode, fingertip, hand_landmarks
