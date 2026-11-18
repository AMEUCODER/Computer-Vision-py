"""Visual effects: smoke/explosion particles, speed lines, headlight cone, vignette."""
import random

import numpy as np
import pygame

from config import WIDTH, HEIGHT


def build_headlight_cone(w=170, h=190):
    """Soft cone of light; the car sits at the bottom-centre of this surface."""
    ys, xs = np.mgrid[0:h, 0:w]
    d = (h - 1 - ys) / h                                  # 0 at the bumper -> 1 far ahead
    half = 0.22 + 0.78 * d
    hx = np.abs(xs - w / 2) / (w / 2)
    alpha = np.clip(1 - hx / half, 0, 1) ** 1.4 * (1 - d) ** 1.2 * 95
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((255, 244, 200, 0))
    px = pygame.surfarray.pixels_alpha(surf)
    px[:, :] = alpha.T.astype(np.uint8)
    del px
    return surf


def build_vignette():
    ys, xs = np.mgrid[0:HEIGHT, 0:WIDTH]
    d = ((xs - WIDTH / 2) / (WIDTH / 2)) ** 2 + ((ys - HEIGHT / 2) / (HEIGHT / 2)) ** 2
    alpha = np.clip((d - 0.45) / 1.1, 0, 1) * 150
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    surf.fill((0, 0, 8, 0))
    px = pygame.surfarray.pixels_alpha(surf)
    px[:, :] = alpha.T.astype(np.uint8)
    del px
    return surf


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size", "grow", "kind")

    def __init__(self, x, y, vx, vy, life, size, grow, kind):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.grow, self.kind = size, grow, kind


class Effects:
    """All particles are drawn onto one shared translucent overlay (one blit per frame)."""

    def __init__(self):
        self.particles = []
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.lines = [[random.uniform(20, WIDTH - 20), random.uniform(0, HEIGHT),
                       random.uniform(30, 90), random.uniform(0.7, 1.3)] for _ in range(16)]
        self._smoke_timer = 0.0

    # --- emitters ----------------------------------------------------------
    def smoke(self, x, y, dt, rate=0.045):
        self._smoke_timer += dt
        while self._smoke_timer >= rate:
            self._smoke_timer -= rate
            self.particles.append(_Particle(
                x + random.uniform(-10, 10), y, random.uniform(-14, 14), random.uniform(40, 80),
                random.uniform(0.35, 0.6), random.uniform(3, 5), 7, "smoke"))

    def explosion(self, x, y):
        for _ in range(46):
            ang, spd = random.uniform(0, 6.283), random.uniform(40, 330)
            self.particles.append(_Particle(
                x, y, np.cos(ang) * spd, np.sin(ang) * spd, random.uniform(0.35, 0.9),
                random.uniform(5, 13), 4, "fire"))
        for _ in range(26):
            ang, spd = random.uniform(0, 6.283), random.uniform(180, 520)
            self.particles.append(_Particle(
                x, y, np.cos(ang) * spd, np.sin(ang) * spd, random.uniform(0.25, 0.6),
                random.uniform(1.5, 3), 0, "spark"))
        for _ in range(16):
            self.particles.append(_Particle(
                x + random.uniform(-26, 26), y + random.uniform(-26, 26), random.uniform(-30, 30),
                random.uniform(-70, -20), random.uniform(1.0, 1.8), random.uniform(10, 18), 16, "smoke"))

    def clear(self):
        self.particles.clear()

    # --- update / draw -----------------------------------------------------
    def update(self, dt, scroll):
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += (p.vy + (scroll * 0.35 if p.kind == "smoke" else 0)) * dt
            if p.kind in ("fire", "spark"):
                p.vx *= 0.96
                p.vy *= 0.96
        self.particles = [p for p in self.particles if p.life > 0]
        for ln in self.lines:
            ln[1] += scroll * 1.6 * ln[3] * dt
            if ln[1] > HEIGHT + 100:
                ln[0], ln[1] = random.uniform(20, WIDTH - 20), -random.uniform(40, 200)

    def draw(self, surf, speed_ratio=0.0):
        ov = self.overlay
        used = False
        if speed_ratio > 0.45:
            ov.fill((0, 0, 0, 0))
            used = True
            a = int(90 * min(1.0, (speed_ratio - 0.45) / 0.55))
            for x, y, length, _ in self.lines:
                pygame.draw.line(ov, (255, 255, 255, a), (int(x), int(y)), (int(x), int(y + length)), 2)
        if self.particles:
            if not used:
                ov.fill((0, 0, 0, 0))
                used = True
            for p in self.particles:
                t = p.life / p.max_life                      # 1 -> 0
                if p.kind == "fire":
                    color = _lerp((200, 45, 20), (255, 170, 40), t) + (int(255 * min(1.0, t * 1.8)),)
                elif p.kind == "spark":
                    color = (255, 235, 150, int(255 * t))
                else:
                    g = int(70 + 40 * t)
                    color = (g, g, g + 6, int(130 * t))
                r = max(1, int(p.size + p.grow * (1 - t)))
                pygame.draw.circle(ov, color, (int(p.x), int(p.y)), r)
        if used:
            surf.blit(ov, (0, 0))
