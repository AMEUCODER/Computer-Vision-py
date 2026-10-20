"""Head-tilt input: webcam thread (HeadTracker) + smoothing/dead-zone (Steering)."""
import math
import threading
import time

from config import (
    CAM_PREVIEW_W, CAM_PREVIEW_H, TILT_RANGE, TILT_DEADZONE, TILT_SMOOTHING,
)

try:                                   # the game still runs (keyboard only) without these
    import cv2
    import mediapipe as mp
except Exception:                      # pragma: no cover
    cv2 = mp = None


class HeadTracker:
    """Reads the webcam in a background thread and publishes the head roll angle."""

    def __init__(self, cam_index=0):
        self.available = False
        self.tilt = 0.0
        self.found = False
        self.frame_rgb = None
        self.lock = threading.Lock()
        self.running = False
        self.cap = None
        self.mesh = None
        self.thread = None

        if cv2 is None or mp is None:
            return
        try:
            cap = cv2.VideoCapture(cam_index)
            if not cap.isOpened():
                cap.release()
                return
            self.mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.cap = cap
        except Exception:
            return

        self.available = True
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    @staticmethod
    def _roll(lx, ly, rx, ry):
        """Roll angle of the eye line, always in (-90, +90) degrees."""
        angle = math.atan2(ry - ly, rx - lx)
        if angle > math.pi / 2:        # eyes reported in swapped order -> no 180 deg jump
            angle -= math.pi
        elif angle < -math.pi / 2:
            angle += math.pi
        return angle

    def _loop(self):
        while self.running:
            try:
                ok, frame = self.cap.read()
                if not ok:
                    time.sleep(0.02)
                    continue
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.mesh.process(rgb)

                found = False
                tilt = None
                if result.multi_face_landmarks:
                    lm = result.multi_face_landmarks[0].landmark
                    h, w, _ = frame.shape
                    lx, ly = lm[33].x * w, lm[33].y * h
                    rx, ry = lm[263].x * w, lm[263].y * h
                    tilt = self._roll(lx, ly, rx, ry)
                    found = True
                    cv2.line(frame, (int(lx), int(ly)), (int(rx), int(ry)), (46, 230, 166), 2)

                preview = cv2.resize(frame, (CAM_PREVIEW_W, CAM_PREVIEW_H))
                preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                with self.lock:
                    if tilt is not None:
                        self.tilt = tilt
                    self.found = found
                    self.frame_rgb = preview_rgb
            except Exception:
                time.sleep(0.05)

    def read(self):
        with self.lock:
            return self.tilt, self.found, self.frame_rgb

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.cap:
            self.cap.release()
        if self.mesh:
            self.mesh.close()


class Steering:
    """Turns the raw head roll into a calm steering value in [-1, +1].

    * low-pass filter    -> no jitter from landmark noise
    * dead-zone          -> car stays put while your head is roughly upright
    * neutral calibration-> whatever pose you start in becomes "straight ahead"
    """

    def __init__(self):
        self.neutral = 0.0
        self.smooth = 0.0
        self.value = 0.0
        self._primed = False

    def calibrate(self):
        self.neutral = self.smooth

    def update(self, tilt, found, dt):
        if found:
            if not self._primed:
                self.smooth = self.neutral = tilt
                self._primed = True
            alpha = 1.0 - math.exp(-TILT_SMOOTHING * dt)
            self.smooth += (tilt - self.smooth) * alpha

        delta = self.smooth - self.neutral
        magnitude = abs(delta) - TILT_DEADZONE
        if magnitude <= 0:
            self.value = 0.0
        else:
            self.value = math.copysign(min(1.0, magnitude / (TILT_RANGE - TILT_DEADZONE)), delta)
        return self.value
