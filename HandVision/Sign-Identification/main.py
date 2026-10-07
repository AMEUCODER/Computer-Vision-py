"""
Live Camera Sign Identification (MediaPipe + rule-based classification)
--------------------------------------------------------------------------
Camera loop only - all detection/classification logic lives in
detection.py, all tunable numbers live in config.py.

NOTE: save this file as main.py inside its own project folder (e.g.
SignIdentifier/main.py) alongside config.py and detection.py - it's named
sign_main.py here only to avoid overwriting the unrelated main.py from
your other gesture-filter project in this same downloads folder.

Install:  pip install opencv-python mediapipe numpy
Run:      python main.py
Press 'q' to quit.
"""

import cv2
from collections import deque, Counter

import config
import detection


def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, config.BUFFER_SIZE)

    history = deque(maxlen=config.HISTORY_SIZE)
    stable_sign = None
    frames_since_hand = 0

    with detection.create_hand_detector() as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            current_sign, hand_landmarks = detection.detect_sign(hands, rgb)

            if hand_landmarks is not None:
                detection.draw_hand_landmarks(frame, hand_landmarks)
                frames_since_hand = 0
            else:
                frames_since_hand += 1

            # --- Smoothing: majority vote over recent readings ---
            if current_sign is not None:
                history.append(current_sign)

            if len(history) >= config.HISTORY_SIZE // 2:
                most_common, count = Counter(history).most_common(1)[0]
                if count >= len(history) * config.MAJORITY_RATIO:
                    stable_sign = most_common

            # Reset the display if the hand's been gone/unrecognized a while,
            # rather than holding onto a stale sign indefinitely.
            if frames_since_hand > config.NO_HAND_RESET_FRAMES:
                stable_sign = None
                history.clear()

            # --- HUD ---
            display_text = stable_sign if stable_sign else "..."
            cv2.putText(frame, display_text, (20, 60),cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3)
            cv2.putText(frame, "'q' to quit", (20, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow("Sign Identification", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()