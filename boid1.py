import math
import random
import pygame

class boid():
    def __init__(self,x,y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.acceleration = pygame.Vector2(0, 0)
        self.max_speed = 4
        self.max_force = 0.1

    def apply_force(self, force):
        self.acceleration += force


    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        elif self.velocity.length() < 1:
            self.velocity.scale_to_length(1)

        self.position += self.velocity

        # 4. Reset acceleration
        self.acceleration *= 0

    def separation(self, school):
        steering = pygame.Vector2(0, 0)
        total = 0
        for other in school:
            d = self.position.distance_to(other.position)
            if other is not self and d < 25:
                # EPSILON SHIELD: Prevent division by zero
                if d < 0.001:
                    diff = pygame.Vector2(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))
                else:
                    diff = (self.position - other.position) / d
                steering += diff
                total += 1

        if total > 0:
            steering /= total
            # ZERO-LENGTH SHIELD: Prevent scale_to_length crash
            if steering.length_squared() < 0.0001:
                steering = pygame.Vector2(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))

            steering.scale_to_length(self.max_speed)
            steering -= self.velocity
            if steering.length_squared() > self.max_force**2:
                steering.scale_to_length(self.max_force)

        # Always return a Vector2, even if it's (0,0)
        return steering

    def cohesion(self, school):
        perception_radius = 50
        steering = pygame.Vector2(0, 0)
        total = 0
        for other in school:
            distance = self.position.distance_to(other.position)
            if other is not self and distance < perception_radius:
                steering += other.position # Add up all positions
                total += 1
        if total > 0:
            steering /= total      # Find the average position (center of mass)
            steering -= self.position # Vector pointing from me to the center
            if steering.length() > 0:
                steering.scale_to_length(self.max_speed)
                steering -= self.velocity
                if steering.length() > self.max_force:
                    steering.scale_to_length(self.max_force)
        return steering

    def avoid_walls(self, width, height):
        margin = 50  # How close to the wall before they start turning
        steering = pygame.Vector2(0, 0)

        # Check X-axis boundaries
        if self.position.x < margin:
            steering.x = self.max_speed
        elif self.position.x > width - margin:
            steering.x = -self.max_speed

        # Check Y-axis boundaries
        if self.position.y < margin:
            steering.y = self.max_speed
        elif self.position.y > height - margin:
            steering.y = -self.max_speed

        # If we need to steer, calculate the force
        if steering.length() > 0:
            steering.scale_to_length(self.max_speed)
            steering -= self.velocity # Steering = Desired - Current
            # Limit the force so the turn is gradual and smooth
            if steering.length() > self.max_force:
                steering.scale_to_length(self.max_force)

        return steering

    def resolve_overlap(self, school):
        for other in school:
            if other is not self:
                dist = self.position.distance_to(other.position)
                if dist < 12: # Sum of radii
                    # 1. Position Fix (The Nudge)
                    if dist > 0:
                        diff = (self.position - other.position).normalize()
                        self.position += diff * ((12 - dist) / 2)

                        # 2. Velocity Fix (The Bounce)
                        # We reflect the velocity based on the collision vector
                        # This makes them "boing" off each other
                        self.velocity = self.velocity.reflect(diff) * 0.8
                    else:
                        self.position += pygame.Vector2(random.uniform(-1,1), random.uniform(-1,1))

    def bounce_edges(self, width, height):
        # Buffer to keep them from getting stuck in the wall
        margin = 50

        # 1. Reflect off Left and Right
        if self.position.x < margin:
            self.velocity.x *= -1
            self.position.x = margin
        elif self.position.x > width - margin:
            self.velocity.x *= -1
            self.position.x = width - margin

        # 2. Reflect off Top and Bottom (The "Reflective" Bottom)
        if self.position.y < margin:
            self.velocity.y *= -1
            self.position.y = margin
        elif self.position.y > height - margin:
            self.velocity.y *= -1
            self.position.y = height - margin

    def draw(self, screen):
        pass

class Fish(boid):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = (112, 173, 173)  # A nice prismarine fish color
        self.max_speed = 3          # Fish usually move a bit slower than birds
        self.max_force = 0.15       # Fish can turn very sharply in water
        self.sway_offset = random.uniform(0, math.pi*2)
        # Frequency: Randomize how fast the tail wags (e.g., 0.015 to 0.025)
        self.sway_speed = random.uniform(0.015, 0.025)

    def draw(self, screen):
        if self.velocity.length() > 0.1:
            # --- THE ONE-LINE SCALE ---
            # Increased to 1.8 for a "slightly bigger" feel
            scale = 0.9

            # 1. Orientation Math
            forward = self.velocity.normalize()
            side = pygame.Vector2(-forward.y, forward.x)

            # 2. Procedural Tail Sway (Slightly faster frequency than the shark)
            t = pygame.time.get_ticks()
            sway_val = math.sin(t * self.sway_speed + self.sway_offset)
            sway = sway_val * (6 * scale)

            # 3. Defining Points for a "Fishy" Silhouette
            nose = self.position + forward * (12 * scale)

            # Upper/Lower Body (The "girth" of the fish)
            upper_mid = self.position + forward * (2 * scale) + side * (5 * scale)
            lower_mid = self.position + forward * (2 * scale) - side * (5 * scale)

            # Tail Peduncle (The narrow bit before the fin)
            tail_base = self.position - forward * (8 * scale)

            # Caudal Fin (Tail) with Sway
            tail_top = self.position - forward * (16 * scale) + side * (7 * scale + sway)
            tail_bot = self.position - forward * (16 * scale) - side * (7 * scale - sway)
            tail_notch = self.position - forward * (12 * scale)

            # 4. Color Palette (Silvery Salmon Blue)
            BODY_COLOR = (140, 165, 190)
            DARK_BACK = (90, 110, 130)

            # 5. DRAWING THE LAYERS

            # Layer 1: Main Body Shape
            fish_points = [
                nose,
                upper_mid,
                tail_base + side * (2 * scale),
                tail_top,
                tail_notch,
                tail_bot,
                tail_base - side * (2 * scale),
                lower_mid
            ]
            pygame.draw.polygon(screen, BODY_COLOR, fish_points)

            # Layer 2: Darker Top/Back (Countershading)
            back_points = [
                nose,
                upper_mid,
                tail_base + side * (1 * scale),
                self.position - forward * (4 * scale)
            ]
            pygame.draw.polygon(screen, DARK_BACK, back_points)

            # Layer 3: Tiny Eye
            eye_pos = self.position + forward * (8 * scale) + side * (2 * scale)
            pygame.draw.circle(screen, (30, 30, 40), (int(eye_pos.x), int(eye_pos.y)), int(1 * scale))

    def update(self, grid, cell_size):
        # 1. SPATIAL LOOKUP: Get only neighbors in a 3x3 grid area
        neighbors = []
        grid_x = int(self.position.x // cell_size)
        grid_y = int(self.position.y // cell_size)

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (grid_x + dx, grid_y + dy)
                if key in grid:
                    neighbors.extend(grid[key])

        # 2. RUN STEERING LOGIC
        # Pass the filtered neighbors list instead of the whole school
        align_force = self.alignment(neighbors)
        # (Repeat for separation and cohesion if you have them)
        self.acceleration += align_force

        # 3. PHYSICS INTEGRATION (Your original logic)
        if self.acceleration.length() > self.max_force:
            self.acceleration.scale_to_length(self.max_force)

        self.velocity += self.acceleration

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.position += self.velocity
        self.acceleration *= 0

    def alignment(self, neighbors):
        perception_radius_sq = 2500 # 50^2 - Squared to avoid sqrt math
        steering = pygame.Vector2(0, 0)
        total = 0

        for other in neighbors:
            if other is not self:
                # Vector from other to self
                diff = self.position - other.position
                # Using length_squared() is much faster than distance_to()
                if diff.length_squared() < perception_radius_sq:
                    steering += other.velocity
                    total += 1

        if total > 0:
            steering /= total
            if steering.length() > 0:
                steering.scale_to_length(self.max_speed)
                steering -= self.velocity
                if steering.length() > self.max_force:
                    steering.scale_to_length(self.max_force)

        return steering

class PredatorFish(Fish):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.scale = 1.0
        self.max_speed = 5.0
        self.max_force = 0.1  # LOWER force = HEAVIER feel (less flickering)
        self.velocity = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.target_fish = None
        self.is_bursting = False
        self.burst_timer = 0
        self.next_burst_time = random.randint(100, 300)
        self.cruise_speed = 3.0
        self.max_burst_speed = 9.0

    def draw(self, screen):
        if self.velocity.length() > 0.1:
            # --- ONE-LINE SCALE ---
            scale = 1.5  # Change this to 1.5, 2.0, etc., to resize everything

            # 1. Orientation Math
            forward = self.velocity.normalize()
            side = pygame.Vector2(-forward.y, forward.x)

            # 2. Procedural Tail Sway (Scaled sway magnitude)
            sway_speed = 0.02 if self.is_bursting else 0.012
            sway_mag = 25 if self.is_bursting else 15
            t = pygame.time.get_ticks()
            sway = math.sin(t * sway_speed + self.sway_offset) * (sway_mag * scale)

            # 3. Defining Points (All offsets multiplied by scale)
            nose = self.position + forward * (60 * scale)

            # Pectoral Fins
            pec_l = self.position + forward * (5 * scale) + side * (30 * scale + sway * 0.3)
            pec_r = self.position + forward * (5 * scale) - side * (30 * scale + sway * 0.3)
            pec_root_l = self.position + forward * (15 * scale) + side * (12 * scale)
            pec_root_r = self.position + forward * (15 * scale) - side * (12 * scale)

            # Thick Tail Section (Peduncle)
            tail_mid = self.position - forward * (15 * scale)

            # 4. Caudal Fin
            tail_tip_top = self.position - forward * (65 * scale) + side * (25 * scale + sway)
            tail_tip_bot = self.position - forward * (65 * scale) - side * (25 * scale - sway)
            tail_notch = self.position - forward * (50 * scale)

            # --- DORSAL FIN POINTS ---
            dorsal_base_start = self.position + forward * (10 * scale)
            dorsal_tip = self.position - forward * (5 * scale) + side * (4 * scale)
            dorsal_base_end = self.position - forward * (15 * scale)

            # COLOR PALETTE
            BROWN_GREY = (90, 85, 80)
            UNDERBELLY = (55, 50, 45)
            DARK_SPINE = (45, 42, 40)

            # LAYER 1: Pectoral Fins
            pygame.draw.polygon(screen, BROWN_GREY, [pec_root_l, pec_l, self.position + side * (5 * scale)])
            pygame.draw.polygon(screen, BROWN_GREY, [pec_root_r, pec_r, self.position - side * (5 * scale)])

            # LAYER 2: The Main Body & Tail
            body_points = [
                nose, pec_root_r,
                tail_mid - side * (15 * scale),
                tail_tip_top, tail_notch, tail_tip_bot,
                tail_mid + side * (15 * scale),
                pec_root_l
            ]
            pygame.draw.polygon(screen, UNDERBELLY, body_points)

            # LAYER 3: Countershading
            spine_points = [
                self.position + forward * (45 * scale),
                self.position + forward * (10 * scale) + side * (12 * scale),
                tail_mid + side * (6 * scale),
                self.position - forward * (50 * scale) + side * (sway * 0.5),
                tail_mid - side * (6 * scale),
                self.position + forward * (10 * scale) - side * (12 * scale)
            ]
            pygame.draw.polygon(screen, DARK_SPINE, spine_points)

            # --- LAYER 4: DORSAL FIN DRAW ---
            pygame.draw.polygon(screen, DARK_SPINE, [dorsal_base_start, dorsal_tip, dorsal_base_end])

            # 5. Detail: Red Eye
            eye_dist_forward = 35 * scale  # How far toward the nose
            eye_dist_side = 4 * scale     # How far from the center spine (Keep this small!)

            eye_pos1 = self.position + (forward * eye_dist_forward) + (side * eye_dist_side)
            eye_pos2 = self.position + (forward * eye_dist_forward) - (side * eye_dist_side)

            # 3. Draw with a small "Socket" or "Shadow"
            # Draw a slightly larger dark circle first to act as a socket
            pygame.draw.circle(screen, (20, 30, 50), (int(eye_pos1.x), int(eye_pos1.y)), int(2.5 * scale))
            pygame.draw.circle(screen, (20, 30, 50), (int(eye_pos2.x), int(eye_pos2.y)), int(2.5 * scale))

            # Draw the actual glowing red eye on top
            pygame.draw.circle(screen, (238, 75, 43), (int(eye_pos1.x), int(eye_pos1.y)), int(1.5 * scale))
            pygame.draw.circle(screen, (238, 75, 43), (int(eye_pos2.x), int(eye_pos2.y)), int(1.5 * scale))

    def hunt(self, school):
        if not school:
            return pygame.Vector2(0, 0)

        # 1. Find the school's center manually
        avg_pos = pygame.Vector2(0, 0)
        for fish in school:
            avg_pos += fish.position
        center = avg_pos / len(school)

        # 2. Vector to center
        to_center = center - self.position
        dist = to_center.length()

        if dist > 0.001:
            # TANGENT (The Orbit Vector)
            orbit_vel = pygame.Vector2(-to_center.y, to_center.x)
            orbit_vel.scale_to_length(self.max_speed)

            # 3. SELECT DESIRED VELOCITY BASED ON DISTANCE
            if dist > 400:
                # Desired: Full speed toward center
                desired = to_center.normalize() * self.max_speed
            elif dist < 300:
                # Desired: Full speed away from center
                desired = -to_center.normalize() * self.max_speed
            else:
                # Desired: Orbiting
                desired = orbit_vel

            # 4. CALCULATE STEERING FORCE (Desired - Current)
            steering = desired - self.velocity

            # Limit force so it doesn't snap instantly
            if steering.length_squared() > self.max_force**2:
                steering.scale_to_length(self.max_force)

            return steering

        return pygame.Vector2(0, 0)

    def avoid_walls(self, width, height):
        margin = 100  # Give the big shark more room to turn
        desired = None

        if self.position.x < margin:
            desired = pygame.Vector2(self.max_speed, self.velocity.y)
        elif self.position.x > width - margin:
            desired = pygame.Vector2(-self.max_speed, self.velocity.y)

        if self.position.y < margin:
            desired = pygame.Vector2(self.velocity.x, self.max_speed)
        elif self.position.y > height - margin:
            desired = pygame.Vector2(self.velocity.x, -self.max_speed)

        if desired:
            steering = desired - self.velocity
            if steering.length() > self.max_force:
                steering.scale_to_length(self.max_force * 2) # Stronger force for walls
            return steering

        return pygame.Vector2(0, 0)

        # In PredatorFish class
    def update(self, mode, grid, cell_size):
        # 1. SPATIAL TARGETING (Vision)
        # The predator checks its current cell + neighbors to find prey
        possible_prey = []
        grid_x = int(self.position.x // cell_size)
        grid_y = int(self.position.y // cell_size)

        # Predators usually have better vision, so we check a 5x5 grid (range -2 to 2)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                key = (grid_x + dx, grid_y + dy)
                if key in grid:
                    possible_prey.extend(grid[key])

        # 2. BURST & HUNT LOGIC
        self.next_burst_time -= 1

        if not self.is_bursting:
            # Re-clamp speed
            if mode == 3:
                self.max_speed, self.max_force = 2, 0.3
            elif mode == 1:
                self.max_speed = 0.8
            else:
                self.max_speed = 4

            # Trigger burst if prey is detected in the local grid
            if mode == 2 and self.next_burst_time <= 0:
                if possible_prey: # Only burst if there's actually fish nearby
                    self.is_bursting = True
                    self.burst_timer = 60
                    self.max_speed = 7
                    if self.velocity.length() > 0:
                        self.velocity.scale_to_length(self.max_speed)

        # 3. BURST TIMER
        if self.is_bursting:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                self.is_bursting = False
                self.next_burst_time = random.randint(150, 500)

        # 4. PHYSICS (Standard Integration)
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.position += self.velocity
        self.acceleration *= 0

    def predator_separation(self, neighbors):
        # 'Hard' radius: They can never get closer than this (e.g., 50px)
        # 'Soft' radius: They start steering away at this distance (e.g., 120px)
        hard_radius = 50
        soft_radius = 120

        steering = pygame.Vector2(0, 0)
        count = 0

        for other in neighbors:
            if other != self:
                diff = self.position - other.position
                dist_sq = diff.length_squared()

                if 0 < dist_sq < (soft_radius**2):
                    dist = math.sqrt(dist_sq)

                    # --- LAYER 1: HARD COLLISION (Prevents Stacking) ---
                    if dist < hard_radius:
                        # Physically push them apart so they don't overlap
                        overlap = (hard_radius - dist)
                        nudge = diff.normalize() * (overlap * 0.5)
                        self.position += nudge
                        other.position -= nudge
                        # Add a slight bounce-off effect to their velocity
                        self.velocity += nudge * 0.1

                    # --- LAYER 2: SOFT STEERING (Natural Movement) ---
                    diff.normalize_ip()
                    diff /= dist # Force is stronger when closer
                    steering += diff
                    count += 1

        if count > 0:
            steering /= count
            if steering.length() > 0:
                steering.scale_to_length(self.max_speed)
                steering -= self.velocity

                # Clamp the steering so it's smooth
                max_force = 0.2
                if steering.length() > max_force:
                    steering.scale_to_length(max_force)

        return steering