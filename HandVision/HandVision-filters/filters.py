"""
filters.py
-----------
All image filter functions used by the finger-count gesture switcher.
Each filter takes a BGR frame (numpy array) and returns a modified BGR frame.

Import get_filters() from this file to get the {finger_count: filter_fn} map.
"""

import cv2
import numpy as np


def apply_sharpen_filter(frame):
    # Convert frame to grayscale for edge computation
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Calculate gradients along X and Y axes
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

    # Combine X and Y gradients and convert back to 8-bit image
    magnitude = cv2.magnitude(sobelx, sobely)
    filtered_frame = cv2.convertScaleAbs(magnitude)
    return filtered_frame


def filter_thermal(frame):
    # 1. Convert to grayscale to measure pixel brightness/intensity
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Map brightness to a Dark Blue -> Red -> Yellow heat map
    thermal_frame = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

    return thermal_frame


def filter_none(frame):
    return frame


def filter_gray(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def filter_sepia(frame):
    kernel = np.array([[0.272, 0.534, 0.131],
                        [0.349, 0.686, 0.168],
                        [0.393, 0.769, 0.189]])
    sepia = cv2.transform(frame, kernel)
    return sepia.clip(50, 255).astype('uint8')


def filter_edges(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def filter_invert(frame):
    return cv2.bitwise_not(frame)


def get_filters():
    """
    Returns the {finger_count: filter_function} map used to pick which
    filter is active based on the detected gesture. Edit this dict to
    change which filter each finger count triggers.
    """
    return {
        0: filter_none,     # fist -> normal
        1: apply_sharpen_filter,  # 1 finger -> cartoon/stylized look
        2: filter_edges,  # 2 fingers -> thermal/heatmap look
        3: filter_thermal,    # 3 fingers -> edge detection
        4: filter_invert,   # 4 fingers -> inverted colors
        5: filter_none,     # open palm -> back to normal
    }


def blur_face(frame):
    # Run face detection on a downscaled copy - Haar cascades get
    # noticeably slower at higher resolution, and we don't need full-res
    # precision just to find a rough face bounding box.
    scale = 0.5
    small = cv2.resize(frame, None, fx=scale, fy=scale)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Scale the detected boxes back up to full-resolution coordinates,
    # then blur that region on the original full-res frame.
    for (x, y, w, h) in faces:
        x, y, w, h = int(x / scale), int(y / scale), int(w / scale), int(h / scale)

        face_roi = frame[y:y + h, x:x + w]

        # Note: ksize (the tuple) must be odd numbers. Higher numbers = blurrier.
        blurred_face = cv2.GaussianBlur(face_roi, (51, 51), 0)

        frame[y:y + h, x:x + w] = blurred_face

    return frame

