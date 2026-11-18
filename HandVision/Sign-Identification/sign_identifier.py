"""
Live Camera Sign Identification (MediaPipe + rule-based classification)
--------------------------------------------------------------------------
This implements "Path A" from the gesture-recognition roadmap: no training
data, just geometric rules over MediaPipe's 21 hand landmarks.

Key upgrade over simple finger-counting: instead of comparing a fingertip's
y-coordinate to its knuckle's y-coordinate (which only works when the hand
is upright), this measures the actual bend ANGLE at each finger's middle
joint. That makes it rotation-invariant - a peace sign held sideways still
gets recognized correctly, not just one held upright.

Recognized signs (starter vocabulary - see classify_sign() to add more):
  Fist, Open Palm, Thumbs Up, Thumbs Down, Peace/Victory, Pointing,
  Rock On, Call Me, I Love You (ASL), OK Sign

Install:  pip install opencv-python mediapipe numpy
Run:      python sign_identifier.py
Press 'q' to quit.
"""

import cv2
import numpy as np
import time
from collections import deque, Counter
import mediapipe as mp

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

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

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

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
        states[name] = angle > EXTEND_ANGLE_THRESHOLD

    # Thumb: same idea, but using its own joint chain (CMC -> MCP -> TIP),
    # since the thumb only has 2 real joints instead of 3.
    thumb_angle = calc_angle(lm_xy(landmarks, 1), lm_xy(landmarks, 2), lm_xy(landmarks, 4))
    states["thumb"] = thumb_angle > THUMB_ANGLE_THRESHOLD

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
    if pinch_distance < OK_PINCH_DISTANCE and middle and ring and pinky:
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
        if thumb_tip_y < wrist_y - THUMB_VERTICAL_MARGIN:
            return "Thumbs Up"
        elif thumb_tip_y > wrist_y + THUMB_VERTICAL_MARGIN:
            return "Thumbs Down"
        else:
            return "Thumb Out"

    return None  # doesn't match any known sign


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    history = deque(maxlen=HISTORY_SIZE)
    stable_sign = None
    frames_since_hand = 0

    with mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,           # fastest model variant
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            current_sign = None

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                landmarks = hand_landmarks.landmark

                states = get_finger_states(landmarks)
                current_sign = classify_sign(landmarks, states)

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )
                frames_since_hand = 0
            else:
                frames_since_hand += 1

            # --- Smoothing: majority vote over recent readings ---
            if current_sign is not None:
                history.append(current_sign)

            if len(history) >= HISTORY_SIZE // 2:
                most_common, count = Counter(history).most_common(1)[0]
                if count >= len(history) * MAJORITY_RATIO:
                    stable_sign = most_common

            # Reset the display if the hand's been gone/unrecognized a while,
            # rather than holding onto a stale sign indefinitely.
            if frames_since_hand > NO_HAND_RESET_FRAMES:
                stable_sign = None
                history.clear()

            # --- HUD ---
            display_text = stable_sign if stable_sign else "..."
            cv2.putText(frame, display_text, (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3)
            cv2.putText(frame, "'q' to quit", (20, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow("Sign Identification", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
