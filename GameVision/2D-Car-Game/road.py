"""Pre-rendered, seamlessly tiling road surface."""
import numpy as np
import pygame

from config import WIDTH, HEIGHT, LANE_WIDTH, LANE_COUNT, LANES, CURB_W

CURB_PERIOD = 40          # both periods divide HEIGHT (720) so the tile wraps cleanly
DASH_PERIOD = 60


def build_road_tile():
    """One full-screen tile: textured asphalt, tyre wear, cracks, curbs and lane dashes."""
    rng = np.random.default_rng(3)
    x = np.arange(WIDTH, dtype=np.float32)

    base = np.array([42, 45, 54], dtype=np.float32)
    edge = np.minimum(x, WIDTH - 1 - x) / (WIDTH / 2)               # 0 at the edges, 1 mid-road
    shade = (0.80 + 0.20 * np.sqrt(edge))[:, None, None]
    wear = np.zeros(WIDTH, dtype=np.float32)
    for lane_x in LANES:                                             # polished tyre tracks
        for off in (-30, 30):
            wear += 5.0 * np.exp(-(((x - (lane_x + off)) / 11.0) ** 2))
    noise = rng.normal(0, 3.2, (WIDTH, HEIGHT, 1)).astype(np.float32)
    px = base * shade + wear[:, None, None] + noise
    surf = pygame.surfarray.make_surface(np.clip(px, 0, 255).astype(np.uint8))

    # hairline cracks (kept away from the tile's top/bottom so the seam stays invisible)
    for _ in range(14):
        cx, cy = int(rng.integers(30, WIDTH - 30)), int(rng.integers(40, HEIGHT - 120))
        pts = [(cx, cy)]
        for _ in range(int(rng.integers(3, 6))):
            cx += int(rng.integers(-12, 13))
            cy += int(rng.integers(8, 24))
            pts.append((cx, cy))
        pygame.draw.lines(surf, (30, 32, 38), False, pts, 1)

    # curbs: red / white blocks on both sides
    for y in range(0, HEIGHT, CURB_PERIOD):
        for side_x in (0, WIDTH - CURB_W):
            pygame.draw.rect(surf, (210, 50, 55), (side_x, y, CURB_W, CURB_PERIOD // 2))
            pygame.draw.rect(surf, (240, 240, 240), (side_x, y + CURB_PERIOD // 2, CURB_W, CURB_PERIOD // 2))
    for side_x in (0, WIDTH - CURB_W):                               # curb shadow on asphalt
        inner = CURB_W if side_x == 0 else WIDTH - CURB_W - 4
        pygame.draw.rect(surf, (28, 30, 36), (inner, 0, 4, HEIGHT))

    # solid edge lines + dashed lane dividers
    for line_x in (CURB_W + 8, WIDTH - CURB_W - 11):
        pygame.draw.rect(surf, (225, 225, 225), (line_x, 0, 3, HEIGHT))
    for i in range(1, LANE_COUNT):
        lx = i * LANE_WIDTH
        for y in range(0, HEIGHT, DASH_PERIOD):
            pygame.draw.rect(surf, (20, 22, 28), (lx - 4, y, 8, 32))   # soft dark rim
            pygame.draw.rect(surf, MARKER, (lx - 3, y, 6, 30), border_radius=2)
    return surf.convert()


MARKER = (236, 236, 236)


def draw_road(target, tile, offset):
    """Scroll the tile downward by `offset` pixels."""
    y = int(offset) % HEIGHT
    target.blit(tile, (0, y))
    target.blit(tile, (0, y - HEIGHT))
