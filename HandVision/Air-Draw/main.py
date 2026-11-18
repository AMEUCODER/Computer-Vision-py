"""
Air Draw - draw in the air using MediaPipe hand tracking + OpenCV
----------------------------------------------------------------------
Camera loop only - hand/gesture detection lives in detection.py, the
drawing surface lives in canvas.py, and every tunable number lives in
config.py.

Gestures:
  ONLY index finger up  -> DRAW (a line follows your fingertip)
  Index + middle up     -> ERASE (a bigger "rubber" follows your fingertip)
  A closed FIST          -> CLEAR the whole canvas

Install:  pip install opencv-python mediapipe numpy
Run:      python main.py
Press 'q' to quit.
"""

import cv2

import config
import detection
from canvas import DrawingCanvas


def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # less internal camera latency

    canvas = DrawingCanvas()

    with detection.create_hand_detector() as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)

            mode, fingertip, hand_landmarks = detection.detect_hand(hands, frame)

            if hand_landmarks is not None:
                detection.draw_hand_landmarks(frame, hand_landmarks)

            display_mode = canvas.update(frame.shape, mode, fingertip)
            combined = canvas.blend_onto(frame)

            cv2.putText(combined, f"Mode: {display_mode}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(combined, "Index=draw | Index+Middle=erase | Fist=clear | 'q' quit",
                        (20, combined.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow("Air Draw", combined)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
