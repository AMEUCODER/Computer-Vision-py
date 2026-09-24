"""
main.py
--------
Camera loop: tracks your hand (fingercount.py), counts extended fingers,
switches the live filter (filters.py) based on the debounced count, and
handles photo/video capture (capture.py):

  - Hold up 1 finger for 5 seconds -> 5-second on-screen countdown ->
    auto-saves a photo (like the Google Pixel camera timer).
  - Press 'f' to start/stop recording the live feed to a video file.

Requires: mediapipe==0.10.21, opencv-python
Run inside your mp_env virtual environment.

Run: python main.py
Press 'q' to quit.
"""

import cv2

# Enable OpenCV's internal SIMD/threading optimizations (on by default on
# most builds, but explicit doesn't hurt and costs nothing).
cv2.setUseOptimized(True)

from fingercount import hands, mp_hands, mp_drawing, count_fingers
from filters import get_filters, filter_none
from capture import GestureCapture

FILTERS = get_filters()

# ---------------------------------------------------------------------------
# DEBOUNCE - prevents filter flicker when the count briefly misreads
# ---------------------------------------------------------------------------
DEBOUNCE_FRAMES = 5     # how many consecutive frames the same count must hold
                         # before the filter actually switches.

# MediaPipe's landmark output is NORMALIZED (0.0-1.0 fractions of image
# width/height), not raw pixels - so we can run detection on a smaller,
# cheaper copy of the frame and the resulting landmarks still map onto
# the full-resolution frame correctly for drawing and finger counting.
# This is one of the biggest single FPS wins available here, since
# MediaPipe's cost scales with input resolution.
DETECTION_SCALE = 0.5   # 0.5 = detect on a half-size copy. Lower = faster
                         # but less accurate at detecting a hand far away
                         # or partially out of frame.

candidate_count = None
candidate_streak = 0
active_filter = filter_none


def main():
    global candidate_count, candidate_streak, active_filter

    gesture_capture = GestureCapture()

    cap = cv2.VideoCapture(0)

    # Request capture resolution from the camera. 1280x720 is the sweet
    # spot: sharp enough to look good, but far cheaper to process every
    # frame than 1080p - MediaPipe, the face detector, and every filter
    # all run on every pixel, so resolution has a big effect on lag.
    # If it still lags on your machine, try 960x540 or 640x480 instead.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Ask the camera driver to keep only 1 frame buffered internally -
    # some backends buffer several frames by default, which adds latency
    # (you see frames from a moment ago) without improving real FPS.
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Read back what the camera actually gave us (may differ from above).
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera capture resolution: {actual_width}x{actual_height}")

    # Size the window to match the real capture resolution instead of a
    # hardcoded value, so the feed is shown at its native size (sharp)
    # rather than stretched or shrunk.
    cv2.namedWindow("Finger Count Filters", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Finger Count Filters", actual_width, actual_height)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)

            # Downscale before color conversion + MediaPipe processing -
            # smaller image = less work for both steps. draw_landmarks()
            # below still draws correctly on the full-res `frame` since
            # MediaPipe's landmarks are normalized (0-1), not pixel-based.
            small = cv2.resize(frame, None, fx=DETECTION_SCALE, fy=DETECTION_SCALE)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            finger_count = None

            if results.multi_hand_landmarks and results.multi_handedness:
                # zip pairs each detected hand's landmarks with its Left/Right label
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    label = handedness.classification[0].label  # 'Left' or 'Right'
                    finger_count = count_fingers(hand_landmarks, label)

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3),
                        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
                    )
                    break  # only process the first detected hand (max_num_hands=1 anyway)

            # --- Debounce the finger count before switching filters ---
            if finger_count is not None:
                if finger_count == candidate_count:
                    candidate_streak += 1
                else:
                    candidate_count = finger_count
                    candidate_streak = 1

                if candidate_streak >= DEBOUNCE_FRAMES and finger_count in FILTERS:
                    active_filter = FILTERS[finger_count]
            else:
                candidate_count = None
                candidate_streak = 0

            output = active_filter(frame)

            # Record the clean filtered frame (before any HUD/countdown text
            # gets drawn on top), so saved videos don't include the overlays.
            gesture_capture.write_video_frame(output)

            # Hold 1 finger for 5s -> countdown -> auto photo capture.
            output = gesture_capture.update_photo_trigger(output, finger_count)

            # Red REC dot while a video is being recorded.
            output = gesture_capture.draw_recording_indicator(output)

            text = f"Fingers: {finger_count if finger_count is not None else '-'}"
            cv2.putText(output, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(output, "'f' record | hold 1 finger 5s = photo | 'q' quit",
                        (10, output.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow('Finger Count Filters', output)

            key = cv2.waitKey(1) & 0xFF
            gesture_capture.handle_key(key, output.shape)

            if key == ord('q'):
                break
    finally:
        gesture_capture.release()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()