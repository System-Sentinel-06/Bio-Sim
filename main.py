import os

import pygame
import random
import math
import sys

from menu import MenuBoid, draw_custom_header, handle_window_controls, draw_animated_dna
from boid1 import Fish, PredatorFish
from boid2 import Bird, PredatorBird
from environment import WaterEffects

WIDTH, HEIGHT = 1920, 1200
FPS = 60

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def build_spatial_grid(entities, cell_size):
    """Organizes all agents into grid buckets for fast lookup."""
    grid = {}
    for e in entities:
        grid_x = int(e.position.x // cell_size)
        grid_y = int(e.position.y // cell_size)
        key = (grid_x, grid_y)
        if key not in grid:
            grid[key] = []
        grid[key].append(e)
    return grid

# --- OCEAN SIMULATION ---
def fish_main(screen, clock, font):
    fish_num = 700
    water = WaterEffects(WIDTH, HEIGHT)
    school = [Fish(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(fish_num)]
    CENTER_POINT = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    mode = 1
    predators = []
    GRID_CELL_SIZE = 100

    HEADER_HEIGHT = 45
    W = screen.get_width()
    close_rect = pygame.Rect(W - 40, (HEADER_HEIGHT - 30) // 2, 30, 30)
    min_rect = pygame.Rect(W - 85, (HEADER_HEIGHT - 30) // 2, 30, 30)
    close_hitbox = close_rect.inflate(20, 20)
    min_hitbox = min_rect.inflate(20, 20)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                handle_window_controls(event, close_hitbox, min_hitbox)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return "FISH_PREVIEW"
                if event.key == pygame.K_1:
                    mode = 1
                    for fish in school:
                        fish.max_speed, fish.max_force = 0.8, 0.03
                elif event.key in [pygame.K_2, pygame.K_3]:
                    mode = 2 if event.key == pygame.K_2 else 3
                    if not predators:
                        gates = [pygame.Vector2(-200, -200), pygame.Vector2(WIDTH+200, -200),
                                 pygame.Vector2(-200, HEIGHT+200), pygame.Vector2(WIDTH+200, HEIGHT+200)]
                        predators = [PredatorFish(g.x, g.y) for g in gates]
                    for fish in school:
                        fish.max_speed, fish.max_force = (3.5, 0.1) if mode == 2 else (5.0, 0.2)

        spatial_grid = build_spatial_grid(school, GRID_CELL_SIZE)
        water.update(school + predators)
        water.draw(screen)

        for p in predators:
            p.apply_force(p.predator_separation(predators) * 2)
            if mode == 1:
                p.apply_force((pygame.Vector2(-600, -600) - p.position).normalize() * p.max_speed - p.velocity)
            elif mode == 3:
                p.is_bursting = False
                p.max_speed = 4
                to_center = (CENTER_POINT - p.position)
                if to_center.length() > 0.001:
                    orbit_dir = pygame.Vector2(-to_center.y, to_center.x).normalize()
                    p.apply_force(orbit_dir * 1.5 + to_center.normalize() * ((to_center.length() - 300) * 0.02))
            else:
                p.apply_force(p.hunt(school))

            p.update(mode, spatial_grid, GRID_CELL_SIZE)
            if mode != 1: p.bounce_edges(WIDTH, HEIGHT)
            p.draw(screen)

        for fish in school:
            gx, gy = int(fish.position.x // GRID_CELL_SIZE), int(fish.position.y // GRID_CELL_SIZE)
            neighbors = [e for dx in [-1,0,1] for dy in [-1,0,1]
                         if (key := (gx+dx, gy+dy)) in spatial_grid
                         for e in spatial_grid[key]]

            flee_force = pygame.Vector2(0, 0)
            sep, coh, ali = 1.5, 0.3, 0.8

            if mode == 2:
                sep, coh, ali = 10.0, 0.5, 1.0
                for p in predators:
                    if fish.position.distance_to(p.position) < 150:
                        flee_force += (fish.position - p.position).normalize() * fish.max_speed * 1.5 - fish.velocity
            elif mode == 3:
                sep, coh, ali = 50.0, 25.0, 3.0
                to_center = (CENTER_POINT - fish.position)
                flee_force = (pygame.Vector2(-to_center.y, to_center.x).normalize() * fish.max_speed * 0.8) + (to_center.normalize() * 2)

            fish.apply_force(flee_force * 2.0)
            fish.apply_force(fish.separation(neighbors) * sep)
            fish.apply_force(fish.cohesion(neighbors) * coh)
            fish.apply_force(fish.alignment(neighbors) * ali)
            fish.update(spatial_grid, GRID_CELL_SIZE)
            fish.bounce_edges(WIDTH, HEIGHT)
            fish.draw(screen)

        display_title = "Fish Sim"
        close_btn, min_btn = draw_custom_header(screen,display_title)
        pygame.display.flip()
        clock.tick(FPS)

# --- AERIAL SIMULATION ---
def bird_main(screen, clock, font):
    mode = "SCOUT"
    birds = [Bird(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(500)]
    predator = PredatorBird(WIDTH // 2, HEIGHT // 2)
    GRID_CELL_SIZE = 220
    current_zoom, target_zoom = 0.6, 0.6
    clouds = [{'pos': pygame.Vector2(random.randint(-3000, 5000), random.randint(-3000, 5000)),
               'size': random.randint(600, 1300), 'depth': random.uniform(0.1, 0.4)} for _ in range(30)]

    HEADER_HEIGHT = 45
    W = screen.get_width()
    close_rect = pygame.Rect(W - 40, (HEADER_HEIGHT - 30) // 2, 30, 30)
    min_rect = pygame.Rect(W - 85, (HEADER_HEIGHT - 30) // 2, 30, 30)
    close_hitbox = close_rect.inflate(20, 20)
    min_hitbox = min_rect.inflate(20, 20)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                handle_window_controls(event, close_hitbox, min_hitbox)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t: mode = "HUNT" if mode == "SCOUT" else "SCOUT"
                if event.key == pygame.K_ESCAPE: return "BIRD_PREVIEW"

        spatial_grid = build_spatial_grid(birds, GRID_CELL_SIZE)
        target_zoom = 1.2 if mode == "HUNT" else 0.6
        current_zoom += (target_zoom - current_zoom) * 0.05
        screen.fill((110, 160, 230))

        # Parallax Clouds
        for c in clouds:
            rel_x = (c['pos'].x - predator.position.x * c['depth']) * current_zoom + (WIDTH // 2)
            rel_y = (c['pos'].y - predator.position.y * c['depth']) * current_zoom + (HEIGHT // 2)
            scaled_size = int(c['size'] * current_zoom)
            if -scaled_size < rel_x < WIDTH + scaled_size:
                c_surf = pygame.Surface((scaled_size, scaled_size//2), pygame.SRCALPHA)
                pygame.draw.ellipse(c_surf, (255, 255, 255, 50), (0, 0, scaled_size, scaled_size//2))
                screen.blit(c_surf, (rel_x, rel_y))

        flock_center = sum((b.position for b in birds), pygame.Vector2(0,0)) / len(birds) if birds else pygame.Vector2(WIDTH//2, HEIGHT//2)

        for b in birds:
            b.update(WIDTH, HEIGHT, spatial_grid, GRID_CELL_SIZE, flock_center, (b == predator.target_bird and mode == "HUNT"), predator)
        predator.update(mode, spatial_grid, GRID_CELL_SIZE, flock_center, WIDTH, HEIGHT)

        all_entities = sorted(birds + [predator], key=lambda e: e.position.y)
        for e in all_entities:
            if isinstance(e, Bird):
                e.draw(screen, predator.position, current_zoom, WIDTH, HEIGHT, (e == predator.target_bird and mode == "HUNT"))
            else:
                e.draw(screen, current_zoom, WIDTH, HEIGHT)

        display_title = "Bird Sim"
        draw_custom_header(screen,display_title)
        pygame.display.flip()
        clock.tick(FPS)

# --- MAIN LAUNCHER ---
def main():
    pygame.init()
    pygame.mixer.init()
    music_file = resource_path("bg_music.mp3")
    pygame.mixer.music.load(music_file)
    icon_image = pygame.image.load(resource_path("dna-icon.png"))
    pygame.display.set_icon(icon_image)
    pygame.display.set_caption("Bio-Sim")
    pygame.mixer.music.play(-1)
    screen = pygame.display.set_mode((1920, 1200),pygame.NOFRAME)
    WIDTH, HEIGHT = screen.get_size()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(["arial", "freesans"], 1, bold=True)
    font2 = pygame.font.SysFont(["arial", "freesans"], 50, bold=True)
    sub_font = pygame.font.SysFont(["arial", "freesans"], 28, bold=True)
    title_font = pygame.font.SysFont(["arial", "freesans"], 40, bold=True)
    display_title = "Bio-Sim"

    # --- SETUP BACKGROUND ---
    # Create 50 boids using our new MenuBoid class
    bg_flock = [MenuBoid(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(400)]
    SIDEBAR_WIDTH = 300
    state = "MENU"

    while state != "QUIT":
        if state == "MENU":
            display_title = "Bio-Sim"
            #pygame.display.set_caption(display_title)
            screen.fill((10, 15, 25)) # Deep Background

            # 1. UPDATE AND DRAW BACKGROUND BOIDS
            for b in bg_flock:
                # Apply the base forces you wrote
                sep = b.separation(bg_flock)
                sep = sep*5
                coh = b.cohesion(bg_flock)
                walls = b.avoid_walls(WIDTH, HEIGHT)

                b.apply_force(sep * 1.5)
                b.apply_force(coh * 0.5)
                b.apply_force(walls * 2.0)

                b.update()
                b.draw(screen)

            # 2. DRAW SIDEBAR PANEL
            pygame.draw.rect(screen, (20, 30, 45), (0, 45, SIDEBAR_WIDTH, HEIGHT))
            pygame.draw.line(screen, (50, 100, 150), (SIDEBAR_WIDTH, 45), (SIDEBAR_WIDTH, HEIGHT), 2)

            mouse_pos = pygame.mouse.get_pos()
            btn_x = 50
            btn_w = 200
            btn_h = 100

            title_rect = pygame.Rect(btn_x,150,btn_w,btn_h)
            title_text = title_font.render("BIOSIM",True, (255,140,0))
            screen.blit(title_text, (title_rect.centerx - title_text.get_width()//2, title_rect.centery - title_text.get_height()//2))
            draw_animated_dna(screen, 150, 700, 400)

            # --- ENCASED PROJECT DESCRIPTION ---
            # Define box dimensions
            desc_box_w = 1000
            desc_box_h = 300

            # Center the box in the space to the right of the sidebar
            # (Total Width - Sidebar) / 2 + Sidebar
            center_x_area = ((WIDTH - SIDEBAR_WIDTH) // 2) + SIDEBAR_WIDTH
            desc_x = center_x_area - (desc_box_w // 2)
            desc_y = (HEIGHT // 2) - (desc_box_h // 2) - 125

            # 1. Create a transparent Surface for the box
            # We use pygame.SRCALPHA to enable the 4th color number (transparency)
            desc_surf = pygame.Surface((desc_box_w, desc_box_h))

            # 2. Draw the minimal transparent yellow background (Alpha = 40)
            # (255, 255, 0) is your Bright Yellow; 40 makes it a very faint tint
            pygame.draw.rect(desc_surf, (10, 15, 25, 0), (0, 0, desc_box_w, desc_box_h), border_radius=20)

            # 3. Draw a solid Bright Yellow rounded border
            pygame.draw.rect(desc_surf, (255, 255, 0), (0, 0, desc_box_w, desc_box_h), width=3, border_radius=20)

            # 4. Render and blit the text onto the transparent surface
            about_lines = [
                "WELCOME TO BIO-SIM!",
                "THIS IS A FUN FLOCKING BEHAVIOR SIMULATION.",
                "IT USES THE BOIDS ALGORITHM TO CREATE NATURAL-LOOKING",
                "MOVEMENT PATTERNS FOR FISH AND BIRDS."
            ]

            for i, line in enumerate(about_lines):
                # Everything is bright yellow to match the box
                text_surf = sub_font.render(line, True, (255, 255, 0))
                # Center text inside the local box surface
                text_x = (desc_box_w // 2) - (text_surf.get_width() // 2)
                desc_surf.blit(text_surf, (text_x, 40 + (i * 45) + 10))

            # 5. Finally, blit the entire box onto the main screen
            screen.blit(desc_surf, (desc_x, desc_y))

            # --- OCEAN BUTTON ---
            box1_rect = pygame.Rect(btn_x, 350, btn_w, btn_h)
            is_hover1 = box1_rect.collidepoint(mouse_pos)

            # Draw a bright glow if hovering
            color1 = (30, 100, 200) if is_hover1 else (25, 45, 70)
            pygame.draw.rect(screen, color1, box1_rect, border_radius=15)
            pygame.draw.rect(screen, (0, 255, 255), box1_rect, width=3, border_radius=15) # Neon border

            txt1 = sub_font.render("FISH SIM", True, (0, 255, 255))
            screen.blit(txt1, (box1_rect.centerx - txt1.get_width()//2, box1_rect.centery - txt1.get_height()//2))

            # --- AERIAL BUTTON ---
            box2_rect = pygame.Rect(btn_x, 500, btn_w, btn_h)
            is_hover2 = box2_rect.collidepoint(mouse_pos)

            color2 = (80, 150, 30) if is_hover2 else (35, 60, 35)
            pygame.draw.rect(screen, color2, box2_rect, border_radius=15)
            pygame.draw.rect(screen, (180, 255, 0), box2_rect, width=3, border_radius=15) # Neon border

            txt2 = sub_font.render("BIRD SIM", True, (180, 255, 0))
            screen.blit(txt2, (box2_rect.centerx - txt2.get_width()//2, box2_rect.centery - txt2.get_height()//2))


            close_btn, min_btn = draw_custom_header(screen,display_title)
            for event in pygame.event.get():
                handle_window_controls(event, close_btn, min_btn)
                if event.type == pygame.QUIT:
                    state = "QUIT"

                # --- NEW CLICKING LOGIC ---
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if box1_rect.collidepoint(event.pos):
                            state = "FISH_PREVIEW"  # Go to briefing first
                        if box2_rect.collidepoint(event.pos):
                            state = "BIRD_PREVIEW"  # Go to briefing first
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "QUIT"
            pygame.display.flip()
            clock.tick(60)

        elif state == "BIRD_PREVIEW":
            display_title = "Bird Sim Preview"
            #pygame.display.set_caption(display_title)
            # 1. Keep drawing the menu background so it doesn't just go black
            screen.fill((10, 15, 25))
            for b in bg_flock:
                b.update(); b.draw(screen)

            # 2. Draw Dark Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200)) # 200 is the transparency
            screen.blit(overlay, (0,0))

            # 3. Draw Explanation Box
            info_rect = pygame.Rect(WIDTH//2 - 400, HEIGHT//2 - 300, 800, 600)
            pygame.draw.rect(screen, (30, 45, 60), info_rect, border_radius=20)
            pygame.draw.rect(screen, (180, 255, 0), info_rect, width=3, border_radius=20)

            # 4. Text Content
            title = font2.render("BIRD FLOCK INFO", True, (180, 255, 0))
            screen.blit(title, (info_rect.centerx - title.get_width()//2, info_rect.y + 40))

            instructions = [
                "• T: Toggle HUNT / SCOUT modes",
                "• ESC: Return to Info Page",
                "• The camera zooms automatically during hunts",
                "• Birds will react to the predator's position",
                "",
                "CLICK TO BEGIN SIMULATION"
            ]

            for i, line in enumerate(instructions):
                text_surf = sub_font.render(line, True, (180, 255, 0))
                screen.blit(text_surf, (info_rect.x + 50, info_rect.y + 150 + (i * 50)))

            close_btn, min_btn = draw_custom_header(screen,display_title)
            # 5. Handle Transition
            for event in pygame.event.get():
                handle_window_controls(event, close_btn, min_btn)
                if event.type == pygame.QUIT: state = "QUIT"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state = "BIRD" # Finally enter the bird simulation
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"
            pygame.display.flip()
            clock.tick(60)

        elif state == "FISH_PREVIEW":
            display_title = "Fish Sim Preview"
            #pygame.display.set_caption(display_title)
            # 1. Background Animation
            screen.fill((10, 15, 25))
            for b in bg_flock:
                b.update(); b.draw(screen)

            # 2. Dark Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0,0))

            # 3. Info Box
            info_rect = pygame.Rect(WIDTH//2 - 400, HEIGHT//2 - 300, 800, 600)
            pygame.draw.rect(screen, (20, 40, 60), info_rect, border_radius=20)
            pygame.draw.rect(screen, (0, 180, 255), info_rect, width=3, border_radius=20)

            # 4. Briefing Content
            title = font2.render("FISH SCHOOL INFO", True, (0, 180, 255))
            screen.blit(title, (info_rect.centerx - title.get_width()//2, info_rect.y + 40))

            instructions = [
                "• Press 1: Peaceful Schooling Mode",
                "• Press 2: Predator Hunting Logic",
                "• Press 3: Activate 'FISHNADO' Vortex",
                "• ESC: Return to Info Page",
                "",
                "The water simulates fluid drag on all entities.",
                "",
                "CLICK TO BEGIN SIMULATION"
            ]

            for i, line in enumerate(instructions):
                text_surf = sub_font.render(line, True, (0, 180, 255))
                screen.blit(text_surf, (info_rect.x + 50, info_rect.y + 150 + (i * 45)))

            close_btn, min_btn = draw_custom_header(screen,display_title)
            # 5. Transition
            for event in pygame.event.get():
                handle_window_controls(event,close_btn,min_btn)
                if event.type == pygame.QUIT: state = "QUIT"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state = "FISH"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "MENU"

            pygame.display.flip()
            clock.tick(60)

        elif state == "FISH":
            display_title = "Fish Sim"
            #pygame.display.set_caption(display_title)
            draw_custom_header(screen,display_title)
            state = fish_main(screen, clock, sub_font)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "FISH_PREVIEW"
        elif state == "BIRD":
            display_title = "Bird Sim"
            #pygame.display.set_caption(display_title)
            draw_custom_header(screen,display_title)
            state = bird_main(screen, clock, sub_font)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        state = "BIRD_PREVIEW"
    pygame.quit()

if __name__ == "__main__":
    main()