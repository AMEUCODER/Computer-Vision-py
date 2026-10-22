# =========================================================
# DETECTION — everything about finding the face and working out
# WHERE on screen each filter should be drawn.
# filters.py doesn't know anything about faces; this file is the
# bridge between "raw landmark points" and "center/width/angle".
# =========================================================

import math
import mediapipe as mp
import config

mp_face_mesh = mp.solutions.face_mesh


def create_face_detector():
    """Creates and returns a MediaPipe Face Mesh detector object."""
    return mp_face_mesh.FaceMesh(
        max_num_faces=config.MAX_NUM_FACES,
        refine_landmarks=config.REFINE_LANDMARKS,
        min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
    )


def get_landmarks(face_mesh, frame_rgb, frame_w, frame_h):
    """
    Runs face mesh detection on an RGB frame.
    Returns a list of 468 (x, y) pixel coordinates, or None if no face found.
    MediaPipe gives landmarks as 0.0-1.0 fractions of the image size,
    so we multiply by frame_w / frame_h to turn them into real pixel positions.
    """
    results = face_mesh.process(frame_rgb)
    if not results.multi_face_landmarks:
        return None

    face = results.multi_face_landmarks[0]
    points = [(int(lm.x * frame_w), int(lm.y * frame_h)) for lm in face.landmark]
    return points


def _eye_line(points):
    """Shared helper: returns (left_eye_point, right_eye_point, distance, angle_degrees)."""
    left = points[config.LEFT_EYE_OUTER]
    right = points[config.RIGHT_EYE_OUTER]
    distance = math.hypot(right[0] - left[0], right[1] - left[1])
    angle = math.degrees(math.atan2(right[1] - left[1], right[0] - left[0]))
    return left, right, distance, angle


def get_glasses_placement(points):
    """
    Works out where/how big/how rotated the glasses should be,
    based on the two outer eye corners.
    Returns (center_xy, width_in_pixels, angle_in_degrees).
    """
    left, right, eye_distance, angle = _eye_line(points)
    center = ((left[0] + right[0]) // 2, (left[1] + right[1]) // 2)
    width = int(eye_distance * 2.0)  # a bit wider than eye-to-eye distance
    return center, width, angle


def get_crown_placement(points):
    """
    Works out where to place the crown: above the forehead point,
    sized/rotated using the same eye line as the glasses.
    """
    left, right, eye_distance, angle = _eye_line(points)
    forehead = points[config.FOREHEAD_TOP]

    width = int(eye_distance * 2.6)  # crown spans wider than the face
    center = (forehead[0], forehead[1] - int(eye_distance * 0.9))  # push up above forehead

    return center, width, angle


def get_mustache_placement(points):
    """Sits between the nose bottom and the mouth, sized to mouth width."""
    _, _, _, angle = _eye_line(points)

    nose_bottom = points[config.NOSE_BOTTOM]
    mouth_left = points[config.MOUTH_LEFT]
    mouth_right = points[config.MOUTH_RIGHT]

    mouth_width = math.hypot(mouth_right[0] - mouth_left[0], mouth_right[1] - mouth_left[1])
    width = int(mouth_width * 1.8)

    # Center it just above the mouth, below the nose
    center = ((mouth_left[0] + mouth_right[0]) // 2,
              (nose_bottom[1] + mouth_left[1]) // 2)

    return center, width, angle


def get_clown_nose_placement(points):
    """Sits right on the nose tip."""
    _, _, eye_distance, angle = _eye_line(points)
    nose_tip = points[config.NOSE_TIP]
    width = int(eye_distance * 0.9)
    return nose_tip, width, angle


def get_devil_horns_placement(points):
    """Sits above the forehead, like the crown but narrower."""
    _, _, eye_distance, angle = _eye_line(points)
    forehead = points[config.FOREHEAD_TOP]
    width = int(eye_distance * 2.0)
    center = (forehead[0], forehead[1] - int(eye_distance * 0.9))
    return center, width, angle


def get_dog_nose_placement(points):
    """Sits on the nose tip, a bit bigger than the clown nose."""
    _, _, eye_distance, angle = _eye_line(points)
    nose_tip = points[config.NOSE_TIP]
    width = int(eye_distance * 1.1)
    return nose_tip, width, angle


def get_dog_ears_placement(points):
    """Sits above the forehead, wider than the crown so the ears stick out past the face."""
    _, _, eye_distance, angle = _eye_line(points)
    forehead = points[config.FOREHEAD_TOP]
    width = int(eye_distance * 3.0)
    center = (forehead[0], forehead[1] - int(eye_distance * 1.0))
    return center, width, angle


# ---------------------------------------------------------------
# HOW TO ADD PLACEMENT FOR A NEW FILTER:
# Write a get_xxx_placement(points) function that returns
# (center, width, angle), using whichever landmark indices you need
# (add new index constants to config.py rather than hardcoding numbers
# here). models.py will call it the same way it calls the two above.
# ---------------------------------------------------------------
