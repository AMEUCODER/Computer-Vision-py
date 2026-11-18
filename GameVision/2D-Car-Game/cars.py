"""Procedural top-down car sprites (sedan, sports car, taxi, truck, police).

Each sprite is drawn once at 3x size and smooth-scaled down (= anti-aliased), then cached.
"""
import pygame

from config import CAR_W, CAR_H

STYLES = ["sedan", "sport", "taxi", "truck", "police"]
STYLE_WEIGHTS = [5, 3, 2, 2, 1]
FIXED_COLORS = {"taxi": (250, 196, 32), "police": (238, 240, 246)}
SS = 3                                   # supersampling factor


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(color, f):
    """f < 1 darkens, f > 1 lightens."""
    if f <= 1:
        return tuple(int(v * f) for v in color)
    return _lerp(color, (255, 255, 255), f - 1)


def _render(style, color):
    color = FIXED_COLORS.get(style, color)
    W, H = CAR_W * SS, CAR_H * SS
    s = pygame.Surface((W, H), pygame.SRCALPHA)

    def R(fx, fy, fw, fh):
        return pygame.Rect(int(fx * W), int(fy * H), int(fw * W), int(fh * H))

    def P(fx, fy):
        return (int(fx * W), int(fy * H))

    rad = int(W * 0.30)

    # wheels
    for fy in (0.15, 0.66):
        for fx in (0.0, 0.86):
            pygame.draw.rect(s, (12, 12, 16), R(fx, fy, 0.14, 0.18), border_radius=int(W * 0.04))
            pygame.draw.rect(s, (46, 46, 56), R(fx + 0.045, fy + 0.025, 0.05, 0.13), border_radius=int(W * 0.02))

    # body: dark outline + main colour
    body = R(0.09, 0.02, 0.82, 0.96)
    pygame.draw.rect(s, shade(color, 0.55), body, border_radius=rad)
    inner = body.inflate(-int(W * 0.05), -int(H * 0.02))
    pygame.draw.rect(s, color, inner, border_radius=rad - int(W * 0.02))

    # shading layer (clipped to the body shape)
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    # NOTE: draw.rect on an SRCALPHA surface overwrites pixels (no blending), so the soft
    # sheen / side shading go first and the opaque paint (stripes, bands) is drawn last.
    pygame.draw.rect(layer, (255, 255, 255, 40), R(0.33, 0.04, 0.34, 0.92), border_radius=int(W * 0.17))
    pygame.draw.rect(layer, (0, 0, 0, 55), R(0.09, 0.05, 0.08, 0.90))
    pygame.draw.rect(layer, (0, 0, 0, 55), R(0.83, 0.05, 0.08, 0.90))
    if style == "sport":
        pygame.draw.rect(layer, (245, 245, 245, 235), R(0.405, 0.02, 0.075, 0.96))
        pygame.draw.rect(layer, (245, 245, 245, 235), R(0.52, 0.02, 0.075, 0.96))
    if style == "police":
        pygame.draw.rect(layer, (30, 70, 190, 255), R(0.0, 0.05, 1.0, 0.13))
        pygame.draw.rect(layer, (30, 70, 190, 255), R(0.0, 0.76, 1.0, 0.13))
    if style == "taxi":
        for i in range(8):
            c = (20, 20, 20, 255) if i % 2 == 0 else (250, 250, 250, 255)
            pygame.draw.rect(layer, c, R(0.09 + i * 0.1025, 0.775, 0.1025, 0.03))
    mask = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), inner, border_radius=rad - int(W * 0.02))
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(layer, (0, 0))

    glass, glint = (22, 32, 50), (82, 110, 150)

    if style == "truck":
        pygame.draw.polygon(s, glass, [P(.27, .15), P(.73, .15), P(.80, .27), P(.20, .27)])
        pygame.draw.polygon(s, glint, [P(.30, .165), P(.45, .165), P(.36, .26), P(.24, .26)])
        pygame.draw.rect(s, shade(color, 1.12), R(0.2, 0.27, 0.6, 0.09), border_radius=int(W * 0.03))
        cargo = R(0.13, 0.39, 0.74, 0.58)
        pygame.draw.rect(s, (160, 164, 176), cargo, border_radius=int(W * 0.05))
        pygame.draw.rect(s, (226, 229, 236), cargo.inflate(-int(W * 0.04), -int(H * 0.02)),
                         border_radius=int(W * 0.04))
        for i in range(1, 6):
            y = cargo.top + int(i * cargo.height / 6)
            pygame.draw.line(s, (170, 174, 186), (cargo.left + int(W * 0.04), y),
                             (cargo.right - int(W * 0.04), y), max(1, SS))
        pygame.draw.rect(s, color, R(0.13, 0.62, 0.74, 0.08))             # company stripe
    else:
        pygame.draw.polygon(s, glass, [P(.27, .29), P(.73, .29), P(.82, .42), P(.18, .42)])
        pygame.draw.polygon(s, glint, [P(.30, .305), P(.46, .305), P(.37, .41), P(.23, .41)])
        pygame.draw.rect(s, shade(color, 1.12), R(0.18, 0.42, 0.64, 0.20), border_radius=int(W * 0.04))
        pygame.draw.polygon(s, glass, [P(.18, .62), P(.82, .62), P(.72, .72), P(.28, .72)])
        pygame.draw.polygon(s, (60, 80, 110), [P(.62, .635), P(.80, .635), P(.72, .715), P(.66, .715)])

    if style == "taxi":
        sign = R(0.36, 0.47, 0.28, 0.065)
        pygame.draw.rect(s, (20, 20, 20), sign.inflate(int(W * 0.02), int(H * 0.012)), border_radius=int(W * 0.02))
        pygame.draw.rect(s, (255, 245, 200), sign, border_radius=int(W * 0.015))
    if style == "police":
        bar = R(0.28, 0.47, 0.44, 0.06)
        pygame.draw.rect(s, (20, 20, 24), bar.inflate(int(W * 0.02), int(H * 0.01)), border_radius=int(W * 0.02))
        pygame.draw.rect(s, (235, 40, 50), (bar.left, bar.top, bar.width // 2, bar.height))
        pygame.draw.rect(s, (50, 110, 255), (bar.centerx, bar.top, bar.width // 2, bar.height))

    if style == "sport":                                                    # rear wing
        pygame.draw.rect(s, (14, 14, 18), R(0.05, 0.885, 0.90, 0.085), border_radius=int(W * 0.02))
        pygame.draw.rect(s, shade(color, 0.8), R(0.07, 0.895, 0.86, 0.035), border_radius=int(W * 0.015))
        pygame.draw.rect(s, (255, 60, 60), R(0.14, 0.945, 0.72, 0.016))
    else:
        for fx in (0.14, 0.66):                                             # tail lights
            pygame.draw.rect(s, (235, 28, 40), R(fx, 0.945, 0.20, 0.028), border_radius=int(W * 0.01))

    for fx in (0.15, 0.65):                                                 # headlights
        pygame.draw.ellipse(s, (255, 246, 196), R(fx, 0.03, 0.20, 0.05))
        pygame.draw.ellipse(s, (255, 255, 255), R(fx + 0.04, 0.038, 0.10, 0.025))
    for fx in (0.015, 0.905):                                               # mirrors
        pygame.draw.rect(s, shade(color, 0.7), R(fx, 0.30, 0.08, 0.05), border_radius=int(W * 0.02))

    return pygame.transform.smoothscale(s, (CAR_W, CAR_H))


def _build_shadow():
    w, h = CAR_W + 16, CAR_H + 16
    small = pygame.Surface((w // 4, h // 4), pygame.SRCALPHA)
    pygame.draw.rect(small, (0, 0, 0, 120), (2, 2, w // 4 - 4, h // 4 - 4), border_radius=5)
    return pygame.transform.smoothscale(small, (w, h))               # upscaling = free blur


class CarSprites:
    def __init__(self):
        self._cache = {}
        self.shadow = _build_shadow()

    def get(self, style, color):
        key = (style, FIXED_COLORS.get(style, color))
        if key not in self._cache:
            self._cache[key] = _render(style, color)
        return self._cache[key]

    def draw(self, surf, x, y, style, color):
        surf.blit(self.shadow, self.shadow.get_rect(center=(x + 5, y + 8)))
        sprite = self.get(style, color)
        surf.blit(sprite, sprite.get_rect(center=(int(x), int(y))))
