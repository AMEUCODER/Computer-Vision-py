"""Game objects that are not UI: traffic cars and hitboxes."""
import random

import pygame

from config import CAR_W, CAR_H, HITBOX_SHRINK, NPC_COLORS
from cars import STYLES, STYLE_WEIGHTS


def hitbox(x, y):
    """Slightly smaller than the sprite so near-misses feel fair."""
    rect = pygame.Rect(0, 0, CAR_W, CAR_H)
    rect.center = (int(x), int(y))
    return rect.inflate(-HITBOX_SHRINK[0], -HITBOX_SHRINK[1])


class TrafficCar:
    def __init__(self, lane_x, speed):
        self.x = lane_x
        self.y = -CAR_H
        self.speed = speed
        self.style = random.choices(STYLES, STYLE_WEIGHTS)[0]
        self.color = random.choice(NPC_COLORS)

    def hitbox(self):
        return hitbox(self.x, self.y)
