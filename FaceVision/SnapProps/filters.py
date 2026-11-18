# =========================================================
# FILTERS — this file has two jobs:
#   1. Build each filter's image (a BGRA picture: Blue, Green, Red,
#      Alpha/transparency). Right now we DRAW these with simple shapes
#      instead of loading real PNG files, so the project runs with
#      zero extra downloads. Swapping in a real image later is easy
#      (see the note at the bottom).
#   2. Blend one of those images onto the live camera frame at the
#      right spot, size, and rotation (overlay_image_alpha).
# =========================================================

import cv2
import numpy as np


def create_glasses_overlay():
    """Builds a simple cartoon 'gangster glasses' image with transparency."""
    w, h = 300, 120
    img = np.zeros((h, w, 4), dtype=np.uint8)  # all transparent to start

    # Two lenses + a bridge connecting them
    cv2.circle(img, (80, 60), 55, (0, 0, 0, 255), -1)
    cv2.circle(img, (220, 60), 55, (0, 0, 0, 255), -1)
    cv2.rectangle(img, (135, 50), (165, 70), (0, 0, 0, 255), -1)

    # Small lighter "shine" spot on each lens so they don't look flat
    cv2.circle(img, (65, 45), 10, (60, 60, 60, 255), -1)
    cv2.circle(img, (205, 45), 10, (60, 60, 60, 255), -1)

    return img


def create_crown_overlay():
    """Builds a simple gold crown image with transparency."""
    w, h = 300, 180
    img = np.zeros((h, w, 4), dtype=np.uint8)

    gold = (0, 215, 255, 255)       # OpenCV uses BGR order, not RGB
    dark_gold = (0, 160, 200, 255)

    # Base band of the crown
    cv2.rectangle(img, (20, 120), (280, 170), gold, -1)

    # Zig-zag crown points
    points = np.array([
        [20, 120], [60, 40], [100, 120],
        [150, 10], [200, 120],
        [240, 40], [280, 120]
    ], dtype=np.int32)
    cv2.fillPoly(img, [points], gold)
    cv2.polylines(img, [points], isClosed=True, color=dark_gold, thickness=3)

    # A few colored "jewels"
    cv2.circle(img, (60, 40), 10, (255, 0, 0, 255), -1)
    cv2.circle(img, (150, 10), 10, (0, 0, 255, 255), -1)
    cv2.circle(img, (240, 40), 10, (255, 0, 0, 255), -1)

    return img


def create_mustache_overlay():
    """Builds a simple black handlebar mustache."""
    w, h = 220, 90
    img = np.zeros((h, w, 4), dtype=np.uint8)
    black = (0, 0, 0, 255)
    clear = (0, 0, 0, 0)  # fully transparent — used to "erase" a gap below

    # Main horizontal band (the part that sits right under the nose)
    cv2.ellipse(img, (110, 50), (100, 20), 0, 0, 360, black, -1)
    # Curled tips above-and-outside each end — this is what reads as "mustache"
    # instead of just a black bar
    cv2.circle(img, (18, 32), 18, black, -1)
    cv2.circle(img, (202, 32), 18, black, -1)
    # Thin gap carved out of the middle-bottom, so it isn't one solid blob
    cv2.ellipse(img, (110, 58), (55, 10), 0, 0, 360, clear, -1)

    return img


def create_clown_nose_overlay():
    """Builds a simple round red clown nose."""
    w, h = 90, 90
    img = np.zeros((h, w, 4), dtype=np.uint8)

    cv2.circle(img, (45, 45), 40, (0, 0, 220, 255), -1)       # red ball
    cv2.circle(img, (30, 30), 10, (120, 120, 255, 255), -1)   # shine highlight

    return img


def create_devil_horns_overlay():
    """Builds two simple red devil horns."""
    w, h = 260, 140
    img = np.zeros((h, w, 4), dtype=np.uint8)
    red = (0, 0, 200, 255)
    dark_red = (0, 0, 120, 255)

    left_horn = np.array([[40, 140], [75, 20], [110, 140]], dtype=np.int32)
    right_horn = np.array([[150, 140], [185, 20], [220, 140]], dtype=np.int32)
    cv2.fillPoly(img, [left_horn, right_horn], red)
    cv2.polylines(img, [left_horn, right_horn], True, dark_red, 3)

    return img


def create_dog_nose_overlay():
    """Builds a simple black dog nose + whisker dots."""
    w, h = 140, 100
    img = np.zeros((h, w, 4), dtype=np.uint8)
    black = (0, 0, 0, 255)

    cv2.ellipse(img, (70, 45), (38, 28), 0, 0, 360, black, -1)  # nose pad
    cv2.circle(img, (58, 35), 6, (60, 60, 60, 255), -1)          # shine
    cv2.line(img, (70, 70), (70, 90), black, 4)                  # center line down to "mouth"

    return img


def create_dog_ears_overlay():
    """Builds two simple brown floppy dog ears."""
    w, h = 300, 160
    img = np.zeros((h, w, 4), dtype=np.uint8)
    brown = (40, 90, 150, 255)
    dark_brown = (20, 60, 110, 255)

    left_ear = np.array([[30, 10], [90, 10], [60, 150]], dtype=np.int32)
    right_ear = np.array([[210, 10], [270, 10], [240, 150]], dtype=np.int32)
    cv2.fillPoly(img, [left_ear, right_ear], brown)
    cv2.polylines(img, [left_ear, right_ear], True, dark_brown, 3)

    return img


# ---------------------------------------------------------------
# REGISTRY: maps a filter name -> the function that builds it.
# This dict is the "database of filters" you'll grow over time.
# Adding filter #3, #4, ... later is just adding one line here
# (see the instructions in config.py for the full steps).
# ---------------------------------------------------------------
# NOTE: no "all" entry here. This dict is only for things that are ONE
# image + ONE placement. "Wear glasses AND a crown" isn't one image —
# it's two separate draw calls — so "all" is handled in models.py instead
# (see FILTER_COMBOS there), not here.
FILTER_BUILDERS = {
    "glasses": create_glasses_overlay,
    "crown": create_crown_overlay,
    "mustache": create_mustache_overlay,
    "clown_nose": create_clown_nose_overlay,
    "devil_horns": create_devil_horns_overlay,
    "dog_nose": create_dog_nose_overlay,
    "dog_ears": create_dog_ears_overlay,
}

# Cache built overlays so we don't redraw the shapes every single frame
# (they never change, so building them once and reusing is free performance).
_overlay_cache = {}


def get_overlay(filter_name):
    """Returns the BGRA overlay image for a filter name, building + caching it once."""
    if filter_name not in _overlay_cache:
        builder = FILTER_BUILDERS[filter_name]
        _overlay_cache[filter_name] = builder()
    return _overlay_cache[filter_name]


def overlay_image_alpha(frame, overlay_bgra, center, width, angle_deg):
    """
    Draws overlay_bgra onto frame:
      - centered at 'center' (x, y) in pixels
      - resized so it is 'width' pixels wide (height scales to match)
      - rotated by 'angle_deg' degrees (so it tilts with head tilt)

    Alpha blending explained: the overlay's 4th channel (alpha) says how
    "solid" each pixel is. alpha=255 -> overlay fully replaces the frame
    pixel. alpha=0 -> frame is untouched. In between -> smooth blend.
    """
    oh, ow = overlay_bgra.shape[:2]
    scale = width / ow
    new_w, new_h = int(ow * scale), int(oh * scale)
    if new_w <= 0 or new_h <= 0:
        return frame

    resized = cv2.resize(overlay_bgra, (new_w, new_h))

    # Rotate the overlay around its own center to match head tilt
    rot_mat = cv2.getRotationMatrix2D((new_w / 2, new_h / 2), -angle_deg, 1.0)
    rotated = cv2.warpAffine(
        resized, rot_mat, (new_w, new_h),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)
    )

    cx, cy = center
    x1, y1 = int(cx - new_w / 2), int(cy - new_h / 2)
    x2, y2 = x1 + new_w, y1 + new_h

    # Clip to the frame's boundaries so we never try to draw off-screen
    frame_h, frame_w = frame.shape[:2]
    ox1, oy1 = max(0, -x1), max(0, -y1)
    ox2, oy2 = new_w - max(0, x2 - frame_w), new_h - max(0, y2 - frame_h)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(frame_w, x2), min(frame_h, y2)

    if x2 <= x1 or y2 <= y1:
        return frame  # overlay would be entirely off-screen

    overlay_crop = rotated[oy1:oy2, ox1:ox2]
    alpha = overlay_crop[:, :, 3:4].astype(float) / 255.0
    overlay_rgb = overlay_crop[:, :, :3].astype(float)

    roi = frame[y1:y2, x1:x2].astype(float)
    blended = overlay_rgb * alpha + roi * (1 - alpha)
    frame[y1:y2, x1:x2] = blended.astype(np.uint8)

    return frame


# ---------------------------------------------------------------
# NOTE — swapping in real PNG images instead of drawn shapes:
# Once you have real transparent PNGs (batman mask, spiderman mask,
# dog/cat ears, etc.), replace a create_xxx_overlay() function with:
#
#     def create_sword_overlay():
#         return cv2.imread("assets/sword.png", cv2.IMREAD_UNCHANGED)
#
# cv2.IMREAD_UNCHANGED keeps the alpha channel. overlay_image_alpha()
# doesn't care whether the BGRA image was drawn or loaded from disk —
# everything downstream stays exactly the same.
# ---------------------------------------------------------------
