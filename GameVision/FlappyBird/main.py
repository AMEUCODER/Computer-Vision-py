import random
import sys
import pygame

from config import (
    WIDTH, HEIGHT, LANES, CAR_W, CAR_H, PLAYER_COLOR, NPC_COLORS,
    INK, DIFFICULTIES, create_engine_loop
)
from score import HighScores, NAME_MAX_LEN
from interface import HeadTracker, Button, draw_road, draw_car

class TrafficCar:
    def __init__(self, lane_x, speed):
        self.x = lane_x
        self.y = -CAR_H
        self.speed = speed
        self.color = random.choice(NPC_COLORS)

    def rect(self):
        return pygame.Rect(self.x - CAR_W // 2, self.y - CAR_H // 2, CAR_W, CAR_H)


def main():
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2)

    tracker = HeadTracker()
    scores = HighScores()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Head-Tilt Traffic Racer")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("couriernew", 36, bold=True)
    font_small = pygame.font.SysFont("couriernew", 18)
    font_btn = pygame.font.SysFont("couriernew", 18, bold=True)

    # Audio & Controls
    music_playing = False
    engine_sound = create_engine_loop()
    current_diff_name = "MEDIUM"

    music_btn = Button((12, 10, 110, 30), "SOUND: OFF")
    diff_btn = Button((130, 10, 140, 30), "MODE: MEDIUM")
    
    start_btn = Button((WIDTH / 2 - 90, HEIGHT / 2 + 40, 180, 48), "START")
    scores_btn = Button((WIDTH / 2 - 90, HEIGHT / 2 + 100, 180, 48), "SCORES")
    back_btn = Button((WIDTH / 2 - 190, HEIGHT - 80, 170, 48), "BACK")
    retry_btn = Button((WIDTH / 2 - 190, HEIGHT / 2 + 60, 170, 48), "RETRY")
    menu_btn = Button((WIDTH / 2 + 20, HEIGHT / 2 + 60, 170, 48), "MENU")

    neutral = 0.0
    state = "menu"
    player_x = WIDTH // 2
    road_offset = 0.0
    traffic = []
    score = 0
    last_spawn = 0.0
    name_text = ""

    def reset():
        nonlocal player_x, traffic, score, last_spawn
        player_x = WIDTH // 2
        traffic = []
        score = 0
        last_spawn = 0.0

    def start_playing():
        nonlocal neutral, state
        neutral = tilt if found else neutral
        reset()
        state = "playing"

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        tilt, found, cam_frame = tracker.read()
        mouse_pos = pygame.mouse.get_pos()

        diff_cfg = DIFFICULTIES[current_diff_name]
        road_speed = diff_cfg["SPEED"]
        spawn_rate = diff_cfg["SPAWN_RATE"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state in ("menu", "dead"):
                    if music_btn.clicked(mouse_pos):
                        music_playing = not music_playing
                        if music_playing:
                            engine_sound.play(-1)
                            music_btn.label = "SOUND: ON"
                            music_btn.active = True
                        else:
                            engine_sound.stop()
                            music_btn.label = "SOUND: OFF"
                            music_btn.active = False
                    elif diff_btn.clicked(mouse_pos):
                        modes = ["EASY", "MEDIUM", "HARD"]
                        current_diff_name = modes[(modes.index(current_diff_name) + 1) % 3]
                        diff_btn.label = f"MODE: {current_diff_name}"

                if state == "menu":
                    if start_btn.clicked(mouse_pos): start_playing()
                    elif scores_btn.clicked(mouse_pos): state = "scores"
                elif state == "dead":
                    if retry_btn.clicked(mouse_pos): start_playing()
                    elif menu_btn.clicked(mouse_pos): state = "menu"
                elif state == "scores":
                    if back_btn.clicked(mouse_pos): state = "menu"

        # Head steering mapping (Tilt angle drives car left/right)
        delta = max(-0.5, min(0.5, tilt - neutral))
        target_x = (WIDTH / 2) + (delta * 600)  # Sensitivity scalar
        player_x += (target_x - player_x) * 10 * dt
        player_x = max(CAR_W // 2, min(WIDTH - CAR_W // 2, player_x))

        if state == "playing":
            road_offset += road_speed * dt
            score += int(dt * 10)

            # Spawn NPC Traffic
            last_spawn += dt
            if last_spawn > spawn_rate:
                lane_x = random.choice(LANES)
                traffic.append(TrafficCar(lane_x, diff_cfg["NPC_SPEED"]))
                last_spawn = 0.0

            # Update NPC cars
            player_rect = pygame.Rect(player_x - CAR_W // 2, HEIGHT - 130 - CAR_H // 2, CAR_W, CAR_H)
            for car in traffic:
                car.y += (road_speed - car.speed) * dt
                if player_rect.colliderect(car.rect()):
                    state = "dead"
            
            traffic[:] = [c for c in traffic if c.y < HEIGHT + CAR_H]

        # --- DRAWING ---
        draw_road(screen, road_offset)

        if state in ("playing", "dead"):
            for car in traffic:
                draw_car(screen, car.x, car.y, car.color)
            draw_car(screen, player_x, HEIGHT - 130, PLAYER_COLOR)
            
            score_surf = font_big.render(f"SCORE: {score}", True, INK)
            screen.blit(score_surf, (16, 50))

        if state == "menu":
            start_btn.draw(screen, font_btn, mouse_pos)
            scores_btn.draw(screen, font_btn, mouse_pos)
        elif state == "dead":
            over = font_big.render("CRASHED!", True, INK)
            screen.blit(over, (WIDTH / 2 - over.get_width() / 2, HEIGHT / 2 - 60))
            retry_btn.draw(screen, font_btn, mouse_pos)
            menu_btn.draw(screen, font_btn, mouse_pos)

        if state in ("menu", "dead"):
            music_btn.draw(screen, font_btn, mouse_pos)
            diff_btn.draw(screen, font_btn, mouse_pos)

        pygame.display.flip()

    engine_sound.stop()
    tracker.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()