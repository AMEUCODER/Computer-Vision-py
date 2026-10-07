# Live Camera Rock-Paper-Scissors (AR Game)

An interactive, real-time Rock-Paper-Scissors game powered by **Python**, **OpenCV**, and **MediaPipe**. This application uses angle-based geometric rules over hand landmarks rather than heavy machine learning training datasets, ensuring fast, reliable sign detection at any hand rotation.

---

## Modular File Structure

The project is organized into a clean, separated architecture:
- **`config.py`**: Global constants, extension angle thresholds, game timing variables, and state definitions.
- **`signID.py`**: Joint angle calculation geometry, finger extension states, and the RPS classification rule engine.
- **`interface.py`**: On-screen UI rendering wrappers and dynamic visual move icons (Rock, Paper, Scissors).
- **`main.py`**: The orchestration entry point managing the game loop, state machine transitions, scoreboard tracking, and the webcam feed.

---

## Prerequisites & Installation

Make sure you have Python installed, then install the required computer vision and machine learning libraries via terminal:

```bash
pip install opencv-python mediapipe numpy