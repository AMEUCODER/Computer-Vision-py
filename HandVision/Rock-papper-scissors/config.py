"""
config.py - Configuration constants for Rock-Paper-Scissors AR Game
"""

# Angle-based extension thresholds
EXTEND_ANGLE_THRESHOLD = 160
THUMB_ANGLE_THRESHOLD = 150

# Live smoothing parameters
HISTORY_SIZE = 10
MAJORITY_RATIO = 0.6

# Game timing (seconds)
COUNTDOWN_SECONDS = 3
SHOOT_FLASH_SECONDS = 0.6
RESULT_DISPLAY_SECONDS = 3.0
CAPTURE_GRACE_SECONDS = 1.5

# Game States
STATE_IDLE = "IDLE"
STATE_COUNTDOWN = "COUNTDOWN"
STATE_SHOOT = "SHOOT"
STATE_RESULT = "RESULT"