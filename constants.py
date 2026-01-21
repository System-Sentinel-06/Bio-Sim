import pygame

# Initialize pygame just enough to get screen info
pygame.init()
info = pygame.display.Info()

# --- Display Constants ---
# Dynamically gets the resolution of the current monitor
WIDTH = info.current_w
HEIGHT = info.current_h
FPS = 60

# --- UI Layout Scaling ---
# Sidebar is 22% of width; other elements scale by height
SIDEBAR_WIDTH = int(WIDTH * 0.22)
UI_PADDING = int(HEIGHT * 0.02)
DNA_CENTER_X = SIDEBAR_WIDTH // 2
HEADER_HEIGHT = int(HEIGHT * 0.04)  # ~45px on 1080p

# --- Font Sizes (Scalable) ---
# Scales font size so it doesn't look tiny on 4K or huge on 720p
FONT_SIZE_L = int(HEIGHT * 0.02)   # Large titles
FONT_SIZE_M = int(HEIGHT * 0.035)   # Headers
FONT_SIZE_S = int(HEIGHT * 0.02)   # Descriptions/Buttons

# --- Simulation Physics ---
BOID_COUNT = 50
VISION_RADIUS = HEIGHT // 12
MAX_SPEED = HEIGHT // 200
FORCE_STRENGTH = 0.05