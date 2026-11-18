"""Central game settings. Constants only: no pygame / numpy code lives here."""
import os

# --- Window & road ---------------------------------------------------------
WIDTH, HEIGHT = 480, 720
FPS = 60
LANE_COUNT = 3
LANE_WIDTH = WIDTH // LANE_COUNT
LANES = [LANE_WIDTH * i + LANE_WIDTH // 2 for i in range(LANE_COUNT)]
CURB_W = 14                      # red/white rumble strip on each side

CAR_W, CAR_H = 64, 108
PLAYER_Y = HEIGHT - 130
HITBOX_SHRINK = (14, 22)         # pixels removed from a car rect -> fairer crashes
CAM_PREVIEW_W, CAM_PREVIEW_H = 160, 120

# --- Colors ----------------------------------------------------------------
ROAD_COLOR = (40, 44, 52)
MARKER_COLOR = (235, 235, 235)
PLAYER_COLOR = (235, 64, 52)
NPC_COLORS = [
    (52, 152, 219), (46, 204, 113), (155, 89, 182), (230, 126, 34),
    (26, 188, 156), (236, 240, 241), (90, 98, 120), (233, 30, 99),
]
INK = (255, 246, 234)
ACCENT = (46, 230, 166)
GOLD = (255, 209, 102)
DANGER = (255, 90, 90)
PANEL = (16, 18, 40)
BTN_FILL = ACCENT
BTN_FILL_HOVER = GOLD
BTN_TEXT = (21, 15, 46)

# --- Files -----------------------------------------------------------------
SCORES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traffic_scores.json")

# --- Difficulty ------------------------------------------------------------
DIFFICULTIES = {
    "EASY":   {"SPEED": 250, "SPAWN_RATE": 1.5, "NPC_SPEED": 100, "SCORE_MULT": 1.0},
    "MEDIUM": {"SPEED": 400, "SPAWN_RATE": 1.1, "NPC_SPEED": 150, "SCORE_MULT": 1.5},
    "HARD":   {"SPEED": 750, "SPAWN_RATE": 0.7, "NPC_SPEED": 200, "SCORE_MULT": 2.5},
}
DIFFICULTY_ORDER = ["EASY", "MEDIUM", "HARD"]
DODGE_BONUS = 10                 # points for every car you successfully pass

# --- Steering (head tilt) --------------------------------------------------
TILT_RANGE = 0.3                # radians of head roll = full steering
TILT_DEADZONE = 0.03             # ignore tiny wobbles around the neutral pose
TILT_SMOOTHING = 11.0             # higher = snappier, lower = smoother
KEY_SPEED = 430                  # px/s when steering with the keyboard
STEER_RESPONSE = 9.0             # how fast the car glides to the target x
