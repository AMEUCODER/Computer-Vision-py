"""Game loop and state machine: menu -> playing -> dead (-> name entry) -> menu / scores."""
import math
import random

import pygame

import music
import sfx
from cars import CarSprites
from config import (
    WIDTH, HEIGHT, FPS, LANES, CAR_W, CAR_H, CURB_W, PLAYER_Y, PLAYER_COLOR, DIFFICULTIES,
    DIFFICULTY_ORDER, DODGE_BONUS, KEY_SPEED, STEER_RESPONSE, INK,
)
from effects import Effects, build_headlight_cone, build_vignette
from entities import TrafficCar, hitbox
from interface import (
    Button, MusicButton, load_fonts, draw_text, draw_title, draw_hud, draw_steer_meter,
    draw_cam_preview, draw_game_over, draw_name_entry, draw_scores, draw_paused,
)
from road import build_road_tile, draw_road
from score import HighScores, NAME_MAX_LEN
from synth import ensure_mixer
from tracker import HeadTracker, Steering

MENU_SCROLL = 130                      # slow, relaxed road speed behind the menu
TOP_SPEED = 700.0                      # used to scale speed lines
NAME_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.")


class Game:
    def __init__(self, tracker=None):
        pygame.init()
        ensure_mixer()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Head-Tilt Traffic Racer")
        self.clock = pygame.time.Clock()
        self.fonts = load_fonts()

        self.tracker = tracker if tracker is not None else HeadTracker()
        self.steering = Steering()
        self.scores = HighScores()

        self.sprites = CarSprites()
        self.road_tile = build_road_tile()
        self.cone = build_headlight_cone()
        self.vignette = build_vignette()
        self.fx = Effects()
        self.scene = pygame.Surface((WIDTH, HEIGHT))

        sfx.init()
        music.preload()                # builds the theme in the background while you look at the menu

        self._build_buttons()
        self.diff = "MEDIUM"
        self.state = "menu"
        self.running = True
        self.t = 0.0
        self.found = False
        self.frame = None
        self.steer = 0.0
        self._reset_round()
        self.road_offset = 0.0
        self.scroll = float(MENU_SCROLL)
        self.shake = 0.0
        self.flash = 0.0

    # ------------------------------------------------------------ setup
    def _build_buttons(self):
        cx = WIDTH // 2
        self.music_btn = MusicButton((WIDTH - 130, 10, 118, 36))
        self.diff_btn = Button((12, 10, 168, 36), "MODE: MEDIUM", "glass")
        self.start_btn = Button((cx - 100, 384, 200, 54), "START")
        self.scores_btn = Button((cx - 100, 450, 200, 54), "SCORES", "glass")
        self.back_btn = Button((cx - 90, HEIGHT - 100, 180, 52), "BACK")
        self.panel_rect = pygame.Rect(cx - 170, 190, 340, 330)
        self.retry_btn = Button((self.panel_rect.x + 20, self.panel_rect.bottom - 76, 140, 52), "RETRY")
        self.menu_btn = Button((self.panel_rect.right - 160, self.panel_rect.bottom - 76, 140, 52), "MENU", "glass")
        self.name_rect = pygame.Rect(cx - 170, 190, 340, 310)
        self.save_btn = Button((cx - 70, self.name_rect.y + 246, 140, 44), "SAVE")

    def _reset_round(self):
        self.player_x = WIDTH / 2
        self.traffic = []
        self.score = 0.0
        self.dodged = 0
        self.spawn_timer = 0.0
        self.final_score = 0
        self.is_best = False
        self.dead_time = 0.0
        self.saved = False
        self.name = ""

    # ------------------------------------------------------------ state changes
    def start_playing(self):
        self.steering.calibrate()               # your current head pose = "straight ahead"
        self._reset_round()
        self.fx.clear()
        self.scroll = float(DIFFICULTIES[self.diff]["SPEED"])
        self.shake = self.flash = 0.0
        self.state = "playing"

    def crash(self, other):
        self.final_score = int(self.score)
        self.is_best = self.final_score > 0 and self.final_score > self.scores.best
        self.dead_time = 0.0
        self.state = "dead"
        mx, my = (self.player_x + other.x) / 2, (PLAYER_Y + other.y) / 2
        self.fx.explosion(mx, my)
        self.shake, self.flash = 1.0, 0.55
        sfx.crash()

    def finish_name_entry(self, save):
        if save:
            self.scores.add(self.name, self.final_score, self.diff)
        self.saved = True                       # never ask twice for the same run
        self.state = "dead"

    def toggle_music(self):
        self.music_btn.toggle()

    def cycle_difficulty(self):
        i = (DIFFICULTY_ORDER.index(self.diff) + 1) % len(DIFFICULTY_ORDER)
        self.diff = DIFFICULTY_ORDER[i]
        self.diff_btn.label = f"MODE: {self.diff}"

    # ------------------------------------------------------------ input
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN:
            self._on_key(e)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self._on_click(e.pos)

    def _on_key(self, e):
        k, s = e.key, self.state
        if s == "name":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.finish_name_entry(True)
            elif k == pygame.K_ESCAPE:
                self.finish_name_entry(False)
            elif k == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif e.unicode and e.unicode.upper() in NAME_CHARS and len(self.name) < NAME_MAX_LEN:
                self.name += e.unicode.upper()
            return

        if k == pygame.K_m:
            self.toggle_music()
        elif k == pygame.K_c:
            self.steering.calibrate()
        elif s == "menu" and k in (pygame.K_RETURN, pygame.K_SPACE):
            self.start_playing()
        elif s == "playing" and k in (pygame.K_ESCAPE, pygame.K_p):
            self.state = "paused"
        elif s == "paused" and k in (pygame.K_ESCAPE, pygame.K_p):
            self.state = "playing"
        elif s == "dead" and k in (pygame.K_RETURN, pygame.K_SPACE):
            self.start_playing()
        elif s in ("dead", "scores") and k == pygame.K_ESCAPE:
            self.state = "menu"

    def _on_click(self, pos):
        s = self.state
        if s == "name":
            if self.save_btn.clicked(pos):
                self.finish_name_entry(True)
            return
        if self.music_btn.clicked(pos):                       # works on every screen
            self.toggle_music()
            return
        if s in ("menu", "dead") and self.diff_btn.clicked(pos):
            self.cycle_difficulty()
        elif s == "menu":
            if self.start_btn.clicked(pos):
                self.start_playing()
            elif self.scores_btn.clicked(pos):
                self.state = "scores"
        elif s == "dead":
            if self.retry_btn.clicked(pos):
                self.start_playing()
            elif self.menu_btn.clicked(pos):
                self.state = "menu"
        elif s == "scores" and self.back_btn.clicked(pos):
            self.state = "menu"

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        tilt, self.found, self.frame = self.tracker.read()
        self.steer = self.steering.update(tilt, self.found, dt)   # keep the filter warm on every screen
        music.update()                                            # starts playback once the build is done

        if self.state == "paused":
            sfx.engine_off()
            return
        if self.state == "playing":
            sfx.engine_on()
            self._update_playing(dt)
        else:
            sfx.engine_off()
            if self.state in ("dead", "name"):
                self._update_dead(dt)
            else:                                                  # menu / scores: lazy scenery scroll
                self.scroll += (MENU_SCROLL - self.scroll) * min(1.0, 3 * dt)
                self.player_x += (WIDTH / 2 - self.player_x) * min(1.0, 6 * dt)

        self.road_offset += self.scroll * dt
        self.fx.update(dt, self.scroll)
        self.shake = max(0.0, self.shake - 2.2 * dt)
        self.flash = max(0.0, self.flash - 2.5 * dt)

    def _steer_player(self, dt):
        keys = pygame.key.get_pressed()
        kb = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        half = WIDTH / 2 - CURB_W - CAR_W / 2 - 6
        if kb:
            self.player_x += kb * KEY_SPEED * dt
        elif self.tracker.available:
            target = WIDTH / 2 + self.steer * half
            self.player_x += (target - self.player_x) * min(1.0, STEER_RESPONSE * dt)
        self.player_x = max(WIDTH / 2 - half, min(WIDTH / 2 + half, self.player_x))

    def _spawn_car(self, cfg):
        """Spawn in a free lane and never close the last open lane (no unavoidable walls)."""
        busy = {c.x for c in self.traffic if c.y < CAR_H * 2.5}
        free = [lx for lx in LANES if lx not in busy]
        if len(busy) >= len(LANES) - 1 or not free:
            return False
        self.traffic.append(TrafficCar(random.choice(free), cfg["NPC_SPEED"]))
        return True

    def _update_playing(self, dt):
        cfg = DIFFICULTIES[self.diff]
        self.scroll = float(cfg["SPEED"])
        self.score += dt * 10 * cfg["SCORE_MULT"]          # keep the fraction: int(dt*10) was always 0
        self._steer_player(dt)

        self.spawn_timer += dt
        if self.spawn_timer >= cfg["SPAWN_RATE"] and self._spawn_car(cfg):
            self.spawn_timer = 0.0

        me = hitbox(self.player_x, PLAYER_Y)
        for car in self.traffic:
            car.y += (self.scroll - car.speed) * dt
            if me.colliderect(car.hitbox()):
                self.crash(car)
                return

        passed = [c for c in self.traffic if c.y >= HEIGHT + CAR_H]
        if passed:
            self.dodged += len(passed)
            self.score += DODGE_BONUS * cfg["SCORE_MULT"] * len(passed)
            self.traffic = [c for c in self.traffic if c.y < HEIGHT + CAR_H]
        self.fx.smoke(self.player_x, PLAYER_Y + CAR_H * 0.45, dt)

    def _update_dead(self, dt):
        self.dead_time += dt
        self.scroll *= max(0.0, 1.0 - 2.5 * dt)            # roll to a stop
        for car in self.traffic:
            car.y += (self.scroll - car.speed) * dt
        self.traffic = [c for c in self.traffic if -CAR_H * 4 < c.y < HEIGHT + CAR_H]
        self.fx.smoke(self.player_x, PLAYER_Y, dt, rate=0.07)
        if (self.state == "dead" and self.dead_time > 0.9 and not self.saved
                and self.scores.qualifies(self.final_score)):
            self.state = "name"

    # ------------------------------------------------------------ drawing
    def _draw_world(self):
        scene = self.scene
        draw_road(scene, self.road_tile, self.road_offset)
        s = self.state

        if s in ("menu", "scores"):
            if s == "menu":
                y = 300 + int(3 * math.sin(self.t * 3))
                scene.blit(self.cone, self.cone.get_rect(midbottom=(WIDTH // 2, y - CAR_H // 2 + 8)))
                self.sprites.draw(scene, WIDTH // 2, y, "sport", PLAYER_COLOR)
        else:
            if s in ("playing", "paused"):
                scene.blit(self.cone, self.cone.get_rect(midbottom=(int(self.player_x), PLAYER_Y - CAR_H // 2 + 8)))
            for car in sorted(self.traffic, key=lambda c: c.y):
                self.sprites.draw(scene, car.x, car.y, car.style, car.color)
            self.sprites.draw(scene, self.player_x, PLAYER_Y, "sport", PLAYER_COLOR)

        self.fx.draw(scene, self.scroll / TOP_SPEED if s == "playing" else 0.0)
        scene.blit(self.vignette, (0, 0))

    def draw(self):
        self._draw_world()
        scr = self.screen
        scr.fill((0, 0, 0))
        ox = oy = 0
        if self.shake > 0:
            amp = int(10 * self.shake)
            ox, oy = random.randint(-amp, amp), random.randint(-amp, amp)
        scr.blit(self.scene, (ox, oy))
        if self.flash > 0:
            veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            veil.fill((255, 240, 220, int(200 * self.flash)))
            scr.blit(veil, (0, 0))

        mouse, f, s = pygame.mouse.get_pos(), self.fonts, self.state
        if s == "menu":
            draw_title(scr, f, self.t)
            self.start_btn.draw(scr, f.mid, mouse)
            self.scores_btn.draw(scr, f.mid, mouse)
            self.diff_btn.draw(scr, f.small, mouse)
            draw_text(scr, f.tiny, "SPACE = start   |   C = recalibrate   |   M = music",
                      (WIDTH // 2, 548), INK)
            draw_cam_preview(scr, f, self.frame, self.found, self.tracker.available,
                             (WIDTH // 2 - 60, HEIGHT - 122))
        elif s in ("playing", "paused"):
            draw_hud(scr, f, int(self.score), max(self.scores.best, int(self.score)), self.diff)
            draw_steer_meter(scr, f, self.steer, self.found, self.tracker.available)
            if s == "paused":
                draw_paused(scr, f)
        elif s == "dead" and self.dead_time > 0.6:
            draw_game_over(scr, f, self.panel_rect, self.final_score, self.scores.best, self.is_best, self.diff)
            self.retry_btn.draw(scr, f.mid, mouse)
            self.menu_btn.draw(scr, f.mid, mouse)
            self.diff_btn.draw(scr, f.small, mouse)
        elif s == "name":
            draw_name_entry(scr, f, self.name_rect, self.final_score, self.name, self.t)
            self.save_btn.draw(scr, f.mid, mouse)
        elif s == "scores":
            draw_scores(scr, f, self.scores.entries)
            self.back_btn.draw(scr, f.mid, mouse)

        if s != "name":
            self.music_btn.draw(scr, f.small, mouse)
        pygame.display.flip()

    # ------------------------------------------------------------ main loop
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)       # cap: no teleporting after a stall
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        self.shutdown()

    def shutdown(self):
        music.stop_music()
        sfx.engine_off()
        self.tracker.stop()
        pygame.quit()
