"""
interface.py - UI components, move icons, and HUD rendering
"""

import cv2

class RPSInterface:
    @staticmethod
    def draw_move_icon(frame, move, center, scale=1.0):
        """Draws a readable icon for Rock/Paper/Scissors at `center`."""
        x, y = center
        color = (255, 255, 255)
        r = int(70 * scale)

        if move == "Rock":
            cv2.circle(frame, (x, y), r, color, 4)
        elif move == "Paper":
            cv2.rectangle(frame, (x - r, y - r), (x + r, y + r), color, 4)
        elif move == "Scissors":
            cv2.line(frame, (x - r, y - r), (x + r, y + r), color, 4)
            cv2.line(frame, (x - r, y + r), (x + r, y - r), color, 4)
            cv2.circle(frame, (x, y), 10, color, -1)
        else:
            cv2.putText(frame, "?", (x - 20, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 4)

        label = move if move else "?"
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cv2.putText(frame, label, (x - text_size[0] // 2, y + r + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)