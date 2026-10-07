"""
signID.py - Hand landmark calculations and RPS classification rule engine
"""

import numpy as np
from config import EXTEND_ANGLE_THRESHOLD, THUMB_ANGLE_THRESHOLD

def calc_angle(a, b, c):
    """Angle (degrees) at point b, formed by segments a-b and c-b."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))


def lm_xy(landmarks, idx):
    return (landmarks[idx].x, landmarks[idx].y)


def get_finger_states(landmarks):
    """{finger_name: bool} - whether each finger is extended, via PIP angle."""
    states = {}
    finger_joints = {
        "index":  (5, 6, 8),
        "middle": (9, 10, 12),
        "ring":   (13, 14, 16),
        "pinky":  (17, 18, 20),
    }
    for name, (mcp, pip, tip) in finger_joints.items():
        angle = calc_angle(lm_xy(landmarks, mcp), lm_xy(landmarks, pip), lm_xy(landmarks, tip))
        states[name] = angle > EXTEND_ANGLE_THRESHOLD

    thumb_angle = calc_angle(lm_xy(landmarks, 1), lm_xy(landmarks, 2), lm_xy(landmarks, 4))
    states["thumb"] = thumb_angle > THUMB_ANGLE_THRESHOLD
    return states


def classify_rps(states):
    """
    Restricts the sign vocabulary to Rock, Paper, and Scissors.
    """
    thumb, index, middle, ring, pinky = (
        states["thumb"], states["index"], states["middle"], states["ring"], states["pinky"]
    )
    pattern = (thumb, index, middle, ring, pinky)

    if pattern == (False, False, False, False, False):
        return "Rock"
    if pattern == (True, True, True, True, True):
        return "Paper"
    if pattern == (False, True, True, False, False):
        return "Scissors"

    return None


def decide_winner(player, computer):
    """Returns 'Player', 'Computer', or 'Tie'."""
    if player == computer:
        return "Tie"
    beats = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    return "Player" if beats[player] == computer else "Computer"