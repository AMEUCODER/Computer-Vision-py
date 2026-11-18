import os
import numpy as np
import pygame

# --- Window & Road Settings ---
WIDTH, HEIGHT = 480, 720
LANE_COUNT = 3
LANE_WIDTH = WIDTH // LANE_COUNT
LANES = [LANE_WIDTH // 2, LANE_WIDTH + LANE_WIDTH // 2, 2 * LANE_WIDTH + LANE_WIDTH // 2]

CAR_W, CAR_H = 70, 100
CAM_PREVIEW_W, CAM_PREVIEW_H = 160, 120

# --- Colors ---
ROAD_COLOR = (40, 44, 52)
MARKER_COLOR = (255, 255, 255)
PLAYER_COLOR = (235, 64, 52)
NPC_COLORS = [(52, 152, 219), (46, 204, 113), (241, 196, 15), (155, 89, 182)]
INK = (255, 246, 234)
BTN_FILL = (46, 230, 166)
BTN_FILL_HOVER = (255, 209, 102)
BTN_TEXT = (21, 15, 46)

# --- Pathing ---
SCORES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traffic_scores.json")

# --- Difficulty Settings ---
DIFFICULTIES = {
    "EASY": {
        "SPEED": 250,
        "SPAWN_RATE": 1.5,
        "NPC_SPEED": 100
    },
    "MEDIUM": {
        "SPEED": 380,
        "SPAWN_RATE": 1.1,
        "NPC_SPEED": 150
    },
    "HARD": {
        "SPEED": 520,
        "SPAWN_RATE": 0.7,
        "NPC_SPEED": 200
    }
}

# --- Sound Synthesizer ---
def create_engine_loop():
    """Generates a funny retro arcade engine hum."""
    sample_rate = 22050
    duration = 2.0
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, False)
    
    # Engine rev sound using low frequency saw wave + noise
    freq = 80  # Hz low pitch
    saw = 0.3 * (2 * (t * freq - np.floor(0.5 + t * freq)))
    noise = 0.05 * np.random.normal(0, 1, total_samples)
    
    buffer = ((saw + noise) * 32767).astype(np.int16)
    stereo_buffer = np.column_stack((buffer, buffer))
    return pygame.sndarray.make_sound(stereo_buffer)