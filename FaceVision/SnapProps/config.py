# =========================================================
# CONFIG — all the settings you might want to tweak live here.
# Nothing in this file "does" anything by itself; it's just values
# that detection.py / filters.py / models.py read.
# =========================================================

# ----- Camera settings -----
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ----- MediaPipe Face Mesh settings -----
MAX_NUM_FACES = 1              # only track one face at a time (faster)
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.5
REFINE_LANDMARKS = True        # more accurate eye landmarks (slightly slower)

# ----- Landmark indices we use for placing filters -----
# MediaPipe Face Mesh gives back 468 points per face. Each constant
# below is just "the index of the point we care about" — look one up
# on a face-mesh landmark-map image if you ever need a new spot.
LEFT_EYE_OUTER = 33
RIGHT_EYE_OUTER = 263
FOREHEAD_TOP = 10
NOSE_TIP = 1
NOSE_BOTTOM = 2
MOUTH_LEFT = 61
MOUTH_RIGHT = 291

# ----- Filter selection keys -----
# Each number key on the keyboard maps to a filter name.
#
# HOW TO ADD A NEW FILTER (e.g. filter #3 = "sword"):
#   1. In filters.py, write a create_sword_overlay() function that
#      returns a BGRA image (see create_glasses_overlay for an example).
#   2. In filters.py, add "sword": create_sword_overlay to FILTER_BUILDERS.
#   3. In detection.py, write a get_sword_placement(points) function
#      that returns (center, width, angle) — where to draw it.
#   4. Add a line here: ord('3'): "sword"
#   5. In models.py, add one "elif current_filter == 'sword':" branch.
# That's the whole process — nothing else needs to change.
FILTER_KEYS = {
    ord('1'): "glasses",
    ord('2'): "crown",
    ord('3'): "all",         # glasses + crown together (see FILTER_COMBOS in models.py)
    ord('4'): "mustache",
    ord('5'): "clown_nose",
    ord('6'): "devil_horns",
    ord('7'): "dog",         # dog ears + dog nose together
    ord('0'): "none",
}

WINDOW_NAME = "AR Face Filters"
