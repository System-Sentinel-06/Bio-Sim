import pygame
import random
import math

class WaterEffects:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bg_surface = pygame.Surface((width, height))
        self.create_gradient_surface()

        # --- FLUID GRID SETUP ---
        self.grid_size = 40  # Size of each fluid cell
        self.cols = width // self.grid_size
        self.rows = height // self.grid_size
        # Stores Vector2 flow for every cell
        self.flow_grid = [[pygame.Vector2(0, 0) for _ in range(self.rows)] for _ in range(self.cols)]

        self.ray_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.bubbles = [
            {
                "pos": pygame.Vector2(random.randint(0, width), random.randint(0, height)),
                "speed": random.uniform(0.5, 2.0),
                "radius": random.randint(1, 3),
                "wiggle": random.uniform(0, 10)
            }
            for _ in range(40)
        ]

    def update(self, agents=[]):
        # 1. Update Bubbles (Standard float logic)
        for b in self.bubbles:
            b["pos"].y -= b["speed"]
            b["wiggle"] += 0.05
            b["pos"].x += math.sin(b["wiggle"]) * 0.3
            if b["pos"].y < -10:
                b["pos"].y = self.height + 10
                b["pos"].x = random.randint(0, self.width)

        # 2. Dissipation (Water slowing down)
        for x in range(self.cols):
            for y in range(self.rows):
                self.flow_grid[x][y] *= 0.94

                # 3. Enhanced Agent Interaction
        for a in agents:
            gx = int(a.position.x // self.grid_size)
            gy = int(a.position.y // self.grid_size)

            if 0 <= gx < self.cols and 0 <= gy < self.rows:
                # Identification: Check for 'hunt' behavior or scale to find the sharks
                is_shark = getattr(a, 'scale', 1.0) >= 1.0 and hasattr(a, 'hunt')

                if is_shark:
                    # Sharks push a massive amount of water
                    push_force = a.velocity * 0.25
                    # Apply to center cell
                    self.flow_grid[gx][gy] += push_force

                    # NEIGHBOR SPREAD: Push water in the 8 cells around the shark
                    # This creates the "Thick" fluid feel you want
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = gx + dx, gy + dy
                            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                                # Neighbors get 50% of the force for a smooth gradient
                                self.flow_grid[nx][ny] += push_force * 0.5
                else:
                    # Small fish only affect their immediate cell
                    self.flow_grid[gx][gy] += a.velocity * 0.05

    def draw(self, screen):
        # 1. Background Gradient
        screen.blit(self.bg_surface, (0, 0))

        # 2. Draw Fluid "Swish" Arcs/Lines
        # We draw subtle lines that represent the water's current
        for x in range(self.cols):
            for y in range(self.rows):
                flow = self.flow_grid[x][y]
                if flow.length_squared() > 0.1:
                    start_pos = (x * self.grid_size, y * self.grid_size)
                    # The line "sweeps" in the direction of the water flow
                    end_pos = (start_pos[0] + flow.x * 4, start_pos[1] + flow.y * 4)

                    # Gradient Ocean Blue color based on flow strength
                    alpha = min(180, int(flow.length() * 40))
                    color = (100, 180, 255, alpha)

                    # Draw a thin, swept line (the "fluid" texture)
                    pygame.draw.line(screen, color, start_pos, end_pos, 1)

        # 3. Bubbles
        for b in self.bubbles:
            pygame.draw.circle(screen, (150, 200, 255), (int(b["pos"].x), int(b["pos"].y)), b["radius"], 1)

        # 4. God Rays
        self.ray_surface.fill((0, 0, 0, 0))
        current_time = pygame.time.get_ticks() * 0.001
        for i in range(3):
            ray_x = (self.width / 3) * i + math.sin(current_time + i) * 50
            points = [(ray_x, 0), (ray_x + 150, 0), (ray_x - 100, self.height)]
            pygame.draw.polygon(self.ray_surface, (255, 255, 255, 25), points)
        screen.blit(self.ray_surface, (0, 0))

    def create_gradient_surface(self):
        top_color = (60, 120, 190)
        bottom_color = (10, 25, 50)
        for y in range(self.height):
            p = y / self.height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * p)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * p)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * p)
            pygame.draw.line(self.bg_surface, (r, g, b), (0, y), (self.width, y))

import pygame
import random

class SkyEffects:
    def __init__(self, WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT):
        self.width = WIDTH
        self.height = HEIGHT
        self.world_w = WORLD_WIDTH
        self.world_h = WORLD_HEIGHT

        # Create a static gradient surface once to save performance
        self.sky_base = pygame.Surface((WIDTH, HEIGHT))
        for y in range(0, HEIGHT, 10):
            # Deep sky blue to a softer horizon blue
            blue_val = max(180, 255 - (y // 15))
            pygame.draw.rect(self.sky_base, (100, 150, blue_val), (0, y, WIDTH, 10))

        # Initialize some random clouds for Parallax
        self.clouds = []
        for _ in range(15):
            self.clouds.append({
                'pos': pygame.Vector2(random.randint(0, self.world_w), random.randint(0, self.world_h)),
                'size': random.randint(150, 400),
                'speed': random.uniform(0.2, 0.5) # Clouds move slower than birds
            })

    def draw(self, screen, camera_offset):
        # 1. Draw the static sky gradient
        screen.blit(self.sky_base, (0, 0))

        # 2. Draw Parallax Clouds
        for cloud in self.clouds:
            # Shift cloud position based on camera but at a slower 'speed'
            # This creates the 3D depth effect (Parallax)
            rel_x = cloud['pos'].x - (camera_offset.x * cloud['speed'])
            rel_y = cloud['pos'].y - (camera_offset.y * cloud['speed'])

            # Simple soft white ellipse
            cloud_rect = (rel_x, rel_y, cloud['size'], cloud['size'] // 2.5)
            # Use a slightly transparent white
            pygame.draw.ellipse(screen, (255, 255, 255, 80), cloud_rect)

        # 3. Draw the Bounded Cliffs (Solid and stationary in the world)
        left_cliff = pygame.Rect(0 - camera_offset.x, 0 - camera_offset.y, 200, self.world_h)
        right_cliff = pygame.Rect(self.world_w - 200 - camera_offset.x, 0 - camera_offset.y, 200, self.world_h)

        # Dark rock color
        pygame.draw.rect(screen, (40, 42, 45), left_cliff)
        pygame.draw.rect(screen, (40, 42, 45), right_cliff)

        # Optional: Add a 'rim light' to the cliff edge so it stands out
        pygame.draw.line(screen, (60, 65, 70), (200 - camera_offset.x, 0), (200 - camera_offset.x, self.height), 2)
        pygame.draw.line(screen, (60, 65, 70), (self.world_w - 200 - camera_offset.x, 0), (self.world_w - 200 - camera_offset.x, self.height), 2)