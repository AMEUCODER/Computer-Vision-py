import math
import threading
import time
import cv2
import mediapipe as mp
import pygame
import numpy as np
from config import (
    WIDTH, HEIGHT, CAM_PREVIEW_W, CAM_PREVIEW_H, CAR_W, CAR_H,
    ROAD_COLOR, MARKER_COLOR, PLAYER_COLOR, INK, BTN_FILL, BTN_FILL_HOVER, BTN_TEXT
)

class HeadTracker:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.tilt = 0.0
        self.found = False
        self.frame_rgb = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.mesh.process(rgb)

            found = False
            tilt = self.tilt
            if result.multi_face_landmarks:
                lm = result.multi_face_landmarks[0].landmark
                h, w, _ = frame.shape
                left = lm[33]
                right = lm[263]
                lx, ly = left.x * w, left.y * h
                rx, ry = right.x * w, right.y * h
                tilt = math.atan2(ry - ly, rx - lx)
                found = True
                cv2.line(frame, (int(lx), int(ly)), (int(rx), int(ry)), (46, 230, 166), 2)

            preview = cv2.resize(frame, (CAM_PREVIEW_W, CAM_PREVIEW_H))
            preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)

            with self.lock:
                self.tilt = tilt
                self.found = found
                self.frame_rgb = preview_rgb

    def read(self):
        with self.lock:
            return self.tilt, self.found, self.frame_rgb

    def stop(self):
        self.running = False
        self.thread.join(timeout=1)
        self.cap.release()
        self.mesh.close()


class Button:
    def __init__(self, rect, label, active=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.active = active

    def draw(self, surf, font, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        color = (255, 180, 50) if self.active else (BTN_FILL_HOVER if hovered else BTN_FILL)
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, INK, self.rect, width=2, border_radius=8)
        text = font.render(self.label, True, BTN_TEXT)
        surf.blit(text, (self.rect.centerx - text.get_width() / 2, self.rect.centery - text.get_height() / 2))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


def draw_road(surf, road_offset):
    surf.fill(ROAD_COLOR)
    # Animated lane dashes
    for lane_x in [WIDTH // 3, (2 * WIDTH) // 3]:
        for y in range(-100, HEIGHT + 100, 40):
            pygame.draw.rect(surf, MARKER_COLOR, (lane_x - 3, y + (int(road_offset) % 40), 6, 20))


def draw_car(surf, x, y, color):
    rect = pygame.Rect(x - CAR_W // 2, y - CAR_H // 2, CAR_W, CAR_H)
    pygame.draw.rect(surf, color, rect, border_radius=8)
    pygame.draw.rect(surf, (20, 20, 20), (rect.left + 5, rect.top + 15, CAR_W - 10, 15), border_radius=4) # Windshield