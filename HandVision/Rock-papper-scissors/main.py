"""
main.py - Main execution loop and state machine for Rock-Paper-Scissors
"""

import cv2
import random
import time
from collections import deque, Counter
import mediapipe as mp

from config import (
    HISTORY_SIZE, MAJORITY_RATIO, COUNTDOWN_SECONDS,
    SHOOT_FLASH_SECONDS, RESULT_DISPLAY_SECONDS, CAPTURE_GRACE_SECONDS,
    STATE_IDLE, STATE_COUNTDOWN, STATE_SHOOT, STATE_RESULT
)
from signID import get_finger_states, classify_rps, decide_winner
from interface import RPSInterface

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    history = deque(maxlen=HISTORY_SIZE)
    live_preview_sign = None

    state = STATE_IDLE
    state_entered_at = time.time()

    player_move = None
    computer_move = None
    round_result = None
    capture_deadline = None

    wins = {"Player": 0, "Computer": 0, "Tie": 0}

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    with mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            current_sign = None
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                landmarks = hand_landmarks.landmark
                states = get_finger_states(landmarks)
                current_sign = classify_rps(states)

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

            if current_sign is not None:
                history.append(current_sign)
            if len(history) >= HISTORY_SIZE // 2:
                most_common, count = Counter(history).most_common(1)[0]
                if count >= len(history) * MAJORITY_RATIO:
                    live_preview_sign = most_common

            now = time.time()
            elapsed = now - state_entered_at
            h, w = frame.shape[:2]

            # --- STATE TRANSITIONS ---
            if state == STATE_IDLE:
                cv2.putText(frame, "Press SPACE to play a round", (20, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                if live_preview_sign:
                    cv2.putText(frame, f"Currently showing: {live_preview_sign}",
                                (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            elif state == STATE_COUNTDOWN:
                remaining = COUNTDOWN_SECONDS - elapsed
                if remaining > 0:
                    count_text = str(int(remaining) + 1)
                    cv2.putText(frame, count_text, (w // 2 - 40, h // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 255, 255), 8)
                else:
                    state = STATE_SHOOT
                    state_entered_at = now
                    capture_deadline = now + CAPTURE_GRACE_SECONDS
                    history.clear()

            elif state == STATE_SHOOT:
                cv2.putText(frame, "SHOOT!", (w // 2 - 160, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 8)

                if elapsed > SHOOT_FLASH_SECONDS:
                    if current_sign is not None:
                        player_move = current_sign
                    elif live_preview_sign is not None and now < capture_deadline:
                        player_move = live_preview_sign

                    if player_move is not None or now >= capture_deadline:
                        computer_move = random.choice(["Rock", "Paper", "Scissors"])
                        if player_move is None:
                            round_result = "Computer"
                        else:
                            round_result = decide_winner(player_move, computer_move)
                        wins[round_result] += 1
                        state = STATE_RESULT
                        state_entered_at = now

            elif state == STATE_RESULT:
                col_y = h // 2 - 40
                RPSInterface.draw_move_icon(frame, player_move, (w // 3, col_y))
                RPSInterface.draw_move_icon(frame, computer_move, (2 * w // 3, col_y))
                cv2.putText(frame, "YOU", (w // 3 - 30, col_y - 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
                cv2.putText(frame, "COMPUTER", (2 * w // 3 - 90, col_y - 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

                if round_result == "Player":
                    result_text, color = "YOU WIN!", (0, 255, 0)
                elif round_result == "Computer":
                    result_text, color = "COMPUTER WINS", (0, 0, 255)
                else:
                    result_text, color = "TIE", (0, 255, 255)

                text_size = cv2.getTextSize(result_text, cv2.FONT_HERSHEY_SIMPLEX, 1.4, 3)[0]
                cv2.putText(frame, result_text, (w // 2 - text_size[0] // 2, col_y + 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)

                if elapsed > RESULT_DISPLAY_SECONDS:
                    state = STATE_IDLE
                    state_entered_at = now
                    player_move = None
                    computer_move = None
                    round_result = None

            # --- SCOREBOARD ---
            score_text = f"You: {wins['Player']}   Computer: {wins['Computer']}   Ties: {wins['Tie']}"
            cv2.putText(frame, score_text, (20, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "SPACE: play   r: reset score   q: quit",
                        (20, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            cv2.imshow("Rock Paper Scissors", frame)

            # Increase waitKey to 25ms to give the OpenCV window more time to register keystrokes
            key = cv2.waitKey(25) & 0xFF

            if key == ord('q') or key == ord('Q'):
                break
            elif key == ord(' ') and state == STATE_IDLE:
                state = STATE_COUNTDOWN
                state_entered_at = time.time()
            elif key == ord('r') or key == ord('R'):
                wins = {"Player": 0, "Computer": 0, "Tie": 0}

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()