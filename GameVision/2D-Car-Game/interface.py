"""UI layer: fonts, buttons (incl. the music button), HUD, panels and screens."""
import math
from types import SimpleNamespace

import pygame

import music
import sfx
from config import (
    WIDTH, HEIGHT, INK, ACCENT, GOLD, DANGER, PANEL, BTN_TEXT, BTN_FILL, BTN_FILL_HOVER,
    CAM_PREVIEW_W, CAM_PREVIEW_H,
)
from score import NAME_MAX_LEN


# ------------------------------------------------------------------ text helpers
def load_fonts():
    names = "bahnschrift,segoeui,arialrounded,verdana,dejavusans,arial"

    def make(size, bold=True):
        return pygame.font.SysFont(names, size, bold=bold)

    return SimpleNamespace(title=make(58), big=make(36), mid=make(24), small=make(17), tiny=make(13, False))


def draw_text(surf, font, text, pos, color=INK, anchor="center", shadow=True):
    img = font.render(str(text), True, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        sh = font.render(str(text), True, (0, 0, 0))
        sh.set_alpha(150)
        surf.blit(sh, rect.move(2, 3))
    surf.blit(img, rect)
    return rect


def draw_outlined(surf, font, text, pos, color, outline=(15, 12, 40), width=3):
    img = font.render(text, True, color)
    edge = font.render(text, True, outline)
    rect = img.get_rect(center=pos)
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                surf.blit(edge, rect.move(dx, dy))
    surf.blit(img, rect)


def draw_panel(surf, rect, alpha=215, border=ACCENT):
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*PANEL, alpha), layer.get_rect(), border_radius=18)
    pygame.draw.rect(layer, (*border, 230), layer.get_rect(), width=2, border_radius=18)
    surf.blit(layer, rect.topleft)


# ------------------------------------------------------------------ buttons
class Button:
    def __init__(self, rect, label, kind="primary"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.kind = kind                      # "primary" (teal) or "glass" (dark)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

    def _colors(self, hovered):
        if self.kind == "glass":
            return ((60, 66, 112) if hovered else (34, 38, 74)), INK
        return (BTN_FILL_HOVER if hovered else BTN_FILL), BTN_TEXT

    def _body(self, surf, hovered):
        fill, text_color = self._colors(hovered)
        face = self.rect.move(0, -2 if hovered else 0)
        pygame.draw.rect(surf, (8, 8, 22), self.rect.move(0, 4), border_radius=12)       # drop shadow
        pygame.draw.rect(surf, fill, face, border_radius=12)
        top = pygame.Rect(face.x + 3, face.y + 3, face.w - 6, face.h // 2 - 3)
        shine = pygame.Surface(top.size, pygame.SRCALPHA)
        pygame.draw.rect(shine, (255, 255, 255, 38), shine.get_rect(), border_radius=9)
        surf.blit(shine, top.topleft)
        pygame.draw.rect(surf, INK if self.kind == "primary" else (110, 120, 190), face, width=2, border_radius=12)
        return face, text_color

    def draw(self, surf, font, mouse_pos):
        face, text_color = self._body(surf, self.rect.collidepoint(mouse_pos))
        draw_text(surf, font, self.label, face.center, text_color, shadow=False)


class MusicButton(Button):
    """Speaker icon + ON/OFF. Clicking toggles the theme song and the sound effects."""

    def __init__(self, rect):
        super().__init__(rect, "MUSIC", kind="glass")

    def toggle(self):
        on = music.toggle_music()
        sfx.set_enabled(on)
        return on

    def draw(self, surf, font, mouse_pos):
        on = music.is_music_on()
        self.kind = "primary" if on else "glass"
        face, text_color = self._body(surf, self.rect.collidepoint(mouse_pos))
        ix, iy = face.x + 20, face.centery
        pygame.draw.polygon(surf, text_color, [(ix - 8, iy - 4), (ix - 3, iy - 4), (ix + 3, iy - 9),
                                               (ix + 3, iy + 9), (ix - 3, iy + 4), (ix - 8, iy + 4)])
        if on:
            for r in (6, 11):
                pygame.draw.arc(surf, text_color, (ix + 2 - r // 2, iy - r, r * 2, r * 2), -0.9, 0.9, 2)
            label = "LOADING" if music.is_loading() else "ON"
        else:
            pygame.draw.line(surf, DANGER, (ix + 7, iy - 6), (ix + 17, iy + 6), 3)
            pygame.draw.line(surf, DANGER, (ix + 17, iy - 6), (ix + 7, iy + 6), 3)
            label = "OFF"
        draw_text(surf, font, label, (face.centerx + 14, face.centery), text_color, shadow=False)


# ------------------------------------------------------------------ screens
def draw_title(surf, fonts, t):
    bob = math.sin(t * 2.2) * 3
    draw_outlined(surf, fonts.title, "TRAFFIC", (WIDTH // 2, 118 + bob), GOLD)
    draw_outlined(surf, fonts.title, "RACER", (WIDTH // 2, 178 + bob), ACCENT)
    draw_text(surf, fonts.small, "TILT YOUR HEAD TO STEER", (WIDTH // 2, 232), INK)


def draw_hud(surf, fonts, score, best, mode):
    draw_panel(surf, (12, 12, 200, 94), alpha=190)
    draw_text(surf, fonts.tiny, "SCORE", (28, 22), (170, 180, 230), anchor="topleft", shadow=False)
    draw_text(surf, fonts.big, f"{score:,}", (28, 34), INK, anchor="topleft")
    draw_text(surf, fonts.tiny, f"BEST {best:,}  |  {mode}", (28, 98), GOLD, anchor="bottomleft", shadow=False)


def draw_steer_meter(surf, fonts, steer, found, camera_available):
    """Tiny gauge at the bottom: how far you are steering + whether the face is seen."""
    cx, y = WIDTH // 2, HEIGHT - 26
    pygame.draw.rect(surf, (10, 10, 28), (cx - 74, y - 5, 148, 10), border_radius=5)
    pygame.draw.rect(surf, (90, 98, 150), (cx - 1, y - 8, 2, 16))
    knob = int(cx + steer * 68)
    pygame.draw.circle(surf, ACCENT if (found or not camera_available) else DANGER, (knob, y), 8)
    pygame.draw.circle(surf, INK, (knob, y), 8, 2)
    if not camera_available:
        text, color = "KEYBOARD: A/D or ARROWS", INK
    elif found:
        text, color = "FACE OK  |  A/D or ARROWS also work", ACCENT
    else:
        text, color = "NO FACE FOUND", DANGER
    draw_text(surf, fonts.tiny, text, (cx, y - 20), color)


def draw_cam_preview(surf, fonts, frame_rgb, found, available, pos):
    x, y = pos
    box = pygame.Rect(x, y, CAM_PREVIEW_W // 2 + 40, CAM_PREVIEW_H // 2 + 30)
    draw_panel(surf, box, alpha=200, border=ACCENT if found else DANGER)
    if available and frame_rgb is not None:
        h, w = frame_rgb.shape[:2]
        img = pygame.image.frombuffer(frame_rgb.tobytes(), (w, h), "RGB")
        img = pygame.transform.smoothscale(img, (box.w - 16, int((box.w - 16) * h / w)))
        surf.blit(img, (box.x + 8, box.y + 8))
        draw_text(surf, fonts.tiny, "FACE OK" if found else "NO FACE", (box.centerx, box.bottom - 10),
                  ACCENT if found else DANGER)
    else:
        draw_text(surf, fonts.tiny, "NO CAMERA", (box.centerx, box.centery - 10), DANGER)
        draw_text(surf, fonts.tiny, "use A/D or arrows", (box.centerx, box.centery + 8), INK)


def draw_game_over(surf, fonts, rect, score, best, is_best, mode):
    draw_panel(surf, rect)
    draw_text(surf, fonts.big, "CRASHED!", (rect.centerx, rect.y + 46), DANGER)
    draw_text(surf, fonts.tiny, "SCORE", (rect.centerx, rect.y + 92), (170, 180, 230), shadow=False)
    draw_text(surf, fonts.title, f"{score:,}", (rect.centerx, rect.y + 130), INK)
    msg = "NEW BEST!" if is_best else f"BEST {best:,}"
    draw_text(surf, fonts.small, f"{msg}   ({mode})", (rect.centerx, rect.y + 180), GOLD)


def draw_name_entry(surf, fonts, rect, score, name, t):
    draw_panel(surf, rect, border=GOLD)
    draw_text(surf, fonts.mid, "NEW HIGH SCORE!", (rect.centerx, rect.y + 40), GOLD)
    draw_text(surf, fonts.big, f"{score:,}", (rect.centerx, rect.y + 90), INK)
    draw_text(surf, fonts.small, "TYPE YOUR NAME", (rect.centerx, rect.y + 135), (170, 180, 230))
    box = pygame.Rect(0, 0, 250, 44)
    box.center = (rect.centerx, rect.y + 180)
    pygame.draw.rect(surf, (8, 8, 24), box, border_radius=10)
    pygame.draw.rect(surf, ACCENT, box, 2, border_radius=10)
    cursor = "_" if int(t * 2) % 2 == 0 and len(name) < NAME_MAX_LEN else " "
    draw_text(surf, fonts.mid, name + cursor, box.center, INK, shadow=False)
    draw_text(surf, fonts.tiny, "ENTER = save    ESC = skip", (rect.centerx, rect.y + 222), (170, 180, 230),
              shadow=False)


def draw_scores(surf, fonts, entries):
    rect = pygame.Rect(30, 120, WIDTH - 60, 400)
    draw_panel(surf, rect)
    draw_text(surf, fonts.big, "HIGH SCORES", (rect.centerx, rect.y + 44), GOLD)
    if not entries:
        draw_text(surf, fonts.small, "NO SCORES YET - GO RACE!", rect.center, INK)
        return
    medal = [GOLD, (205, 212, 224), (214, 140, 82), INK, INK]
    for i, e in enumerate(entries):
        y = rect.y + 110 + i * 56
        row = pygame.Rect(rect.x + 18, y - 22, rect.w - 36, 46)
        pygame.draw.rect(surf, (28, 32, 66), row, border_radius=10)
        draw_text(surf, fonts.mid, f"{i + 1}", (row.x + 22, row.centery), medal[i], shadow=False)
        draw_text(surf, fonts.mid, e["name"], (row.x + 52, row.centery), INK, anchor="midleft", shadow=False)
        draw_text(surf, fonts.mid, f"{e['score']:,}", (row.right - 12, row.centery - 5), medal[i],
                  anchor="midright", shadow=False)
        if e.get("mode"):
            draw_text(surf, fonts.tiny, e["mode"], (row.right - 12, row.bottom - 8), (150, 160, 215),
                      anchor="midright", shadow=False)


def draw_paused(surf, fonts):
    veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    veil.fill((0, 0, 10, 150))
    surf.blit(veil, (0, 0))
    draw_outlined(surf, fonts.title, "PAUSED", (WIDTH // 2, HEIGHT // 2 - 20), GOLD)
    draw_text(surf, fonts.small, "ESC / P to resume", (WIDTH // 2, HEIGHT // 2 + 34), INK)
