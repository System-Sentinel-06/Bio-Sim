import math
import random
import pygame
from boid1 import boid
import constants

class MenuBoid(boid):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.position = pygame.Vector2(x, y)
        self.max_speed = 100
        self.color = random.choice([
            (0, 212, 255),  # Electric Blue
            (255, 140, 0),  # Bright Orange
            (0, 255, 0)])   # Bright Green

    def update_color(self, title_text):
        if "FISH" in title_text.upper():
            self.color = (0,212, 255)
        elif "BIRD" in title_text.upper():
            self.color = (0, 255, 0)
        else:
            self.color = random.choice([
                (0, 212, 255),  # Electric Blue
                (255, 140, 0),  # Bright Orange
                (0, 255, 0)])   # Bright Green
    def get_gradient_color(self,t):
        # Your 3 specific colors
        c1 = (0, 212, 255)  # Electric Blue
        c2 = (255, 140, 0)  # Bright Orange
        c3 = (0, 255, 0)    # Bright Green

        if t < 0.5:
            # Scale t from [0, 0.5] to [0, 1] for the first half
            local_t = t * 2
            return tuple(int(c1[i] + (c2[i] - c1[i]) * local_t) for i in range(3))
        else:
            # Scale t from [0.5, 1] to [0, 1] for the second half
            local_t = (t - 0.5) * 2
            return tuple(int(c2[i] + (c3[i] - c2[i]) * local_t) for i in range(3))


    def draw(self, screen):
        # Calculate triangle points based on velocity direction
        if self.velocity.length() > 0:
            direction = self.velocity.normalize()
            perp = pygame.Vector2(-direction.y, direction.x) * 5
            tip = self.position + direction * 10
            base1 = self.position - direction * 5 + perp
            base2 = self.position - direction * 5 - perp

            # Create a small surface for alpha transparency
            points = [tip, base1, base2]
            pygame.draw.polygon(screen, self.color, points)

def draw_custom_header(screen, title_text):
    font = pygame.font.SysFont('Arial', 25)
    symbol_font2 = pygame.font.SysFont('Arial', 12, bold=True)
    HEADER_HEIGHT = 45

    # 1. Setup Colors
    title_color = (255, 255, 0)
    if "FISH" in title_text.upper():
        title_color = (0, 180, 255)
    elif "BIRD" in title_text.upper():
        title_color = (180, 255, 0)

    # 2. Create Background Surface
    header_surf = pygame.Surface((constants.WIDTH, HEADER_HEIGHT), pygame.SRCALPHA)

    # Logic for simulation vs menu background
    is_sim = title_text.upper() in ["FISH SIM", "BIRD SIM"]

    if is_sim:
        header_surf.fill((10, 20, 35, 204))
    else:
        header_surf.fill((10, 20, 35, 160))
        for i in range(-HEADER_HEIGHT, constants.WIDTH, 24):
            pygame.draw.line(header_surf, (*title_color, 40), (i, 0), (i + HEADER_HEIGHT, HEADER_HEIGHT), 5)

    # 3. Add Glow Border and BLIT
    pygame.draw.line(header_surf, title_color, (0, HEADER_HEIGHT-1), (constants.WIDTH, HEADER_HEIGHT-1), 2)
    screen.blit(header_surf, (0, 0))

    # 4. RENDER TEXT
    title_surf = font.render(title_text.upper(), True, title_color)
    screen.blit(title_surf, (constants.WIDTH // 2 - title_surf.get_width() // 2, 10))

    # 5. WINDOW CONTROLS LOGIC
    mx, my = pygame.mouse.get_pos()
    close_rect = pygame.Rect(constants.WIDTH - 32, (HEADER_HEIGHT - 25) // 2, 25, 25)
    min_rect = pygame.Rect(constants.WIDTH - 77, (HEADER_HEIGHT - 25) // 2, 25, 25)

    # Hitbox for the event loop
    close_hitbox = close_rect.inflate(20, 20)

    # 6. CONDITIONAL DRAWING
    # Only draw the buttons if we are NOT in the simulation
    if not is_sim:
        c_color = (255, 50, 50) if close_rect.collidepoint(mx, my) else title_color
        m_color = (123, 0, 247) if min_rect.collidepoint(mx, my) else title_color

        pygame.draw.rect(screen, title_color, close_rect, 1)
        pygame.draw.rect(screen, title_color, min_rect, 1)

        c_surf = symbol_font2.render("X", True, c_color)
        m_surf = symbol_font2.render("—", True, m_color)

        screen.blit(c_surf, (close_rect.centerx - c_surf.get_width() // 2,
                             close_rect.centery - c_surf.get_height() // 2))
        screen.blit(m_surf, (min_rect.centerx - m_surf.get_width() // 2,
                             min_rect.centery - m_surf.get_height() // 2))

    # Always return the hitboxes so handle_window_controls doesn't crash
    return close_hitbox, min_rect

def handle_window_controls(event, close_rect, min_rect):
    """
    Handles the logic for the custom X and Minimize buttons.
    Call this inside your event loop.
    """
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Check if the click was inside the Close button area
        if close_rect.collidepoint(event.pos):
            pygame.quit()
            import sys
            sys.exit()

        # Check if the click was inside the Minimize button area
        if min_rect.collidepoint(event.pos):
            # This sends the command to GNOME to hide the window in the dock
            pygame.display.iconify()

def draw_animated_dna(screen, center_x, start_y, height):
    """
    Draws a vertical, rotating DNA double-helix.
    :param center_x: Horizontal center of the DNA strand.
    :param start_y: The top starting point of the strand.
    :param height: How far down the strand should go.
    """
    # Your project colors
    colors = [(0, 212, 255), (255, 140, 0), (0, 255, 0)]

    nodes = 20          # Number of base-pair 'rungs'
    spacing = height // nodes
    amplitude = 30      # How wide the DNA twists
    time_factor = pygame.time.get_ticks() * 0.003 # Rotation speed

    for i in range(nodes):
        current_y = start_y + (i * spacing)

        # Calculate horizontal positions using sine and cosine for the '3D' twist
        # Adding math.pi to x2 puts it exactly on the opposite side (out of phase)
        angle = time_factor + (i * 0.5)
        x1 = center_x + math.sin(angle) * amplitude
        x2 = center_x + math.sin(angle + math.pi) * amplitude

        # Determine color cycling based on the node index
        color = colors[i % len(colors)]

        # 1. Draw the horizontal 'Base Pair' connection
        # We use a lower alpha or thinner line to give it depth
        pygame.draw.line(screen, (100, 100, 100), (x1, current_y), (x2, current_y), 1)

        # 2. Draw the two 'Sugar-Phosphate' backbones (the dots)
        # We draw x1 and x2 dots to represent the two strands
        pygame.draw.circle(screen, color, (int(x1), current_y), 4)
        pygame.draw.circle(screen, color, (int(x2), current_y), 4)