import math
import random
import pygame

class Bird:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-4, 4), random.uniform(-4, 4))
        self.acceleration = pygame.Vector2(0, 0)
        self.scale = 1.6
        self.current_dir = pygame.Vector2(1, 0)

        # --- NATURAL FLUTTER VARIABLES ---
        # Randomize flap speed so they don't look like a machine
        self.flap_speed = random.uniform(0.18, 0.28)
        # Unique seeds for random 'wandering'
        self.noise_seed = random.uniform(0, 1000)
        self.noise_speed = random.uniform(0.01, 0.03)

    def apply_force(self, force):
        self.acceleration += force

    def update(self, WIDTH, HEIGHT, grid, cell_size, flock_center, is_targeted, predator):
        # 1. INITIALIZE PERSISTENT ATTRIBUTES
        if not hasattr(self, 'panic_timer'): self.panic_timer = 0
        if not hasattr(self, 'panic_dir'): self.panic_dir = pygame.Vector2(0, 0)

        # 2. SPATIAL NEIGHBOR LOOKUP (Replaces the loop through all birds)
        neighbors = []
        grid_x = int(self.position.x // cell_size)
        grid_y = int(self.position.y // cell_size)

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (grid_x + dx, grid_y + dy)
                if key in grid:
                    neighbors.extend(grid[key])

        # 3. SETUP VECTORS & OPTIMIZED NEIGHBOR LOOP
        sep = pygame.Vector2(0, 0)
        ali = pygame.Vector2(0, 0)
        coh = pygame.Vector2(0, 0)
        neighbor_count = 0
        radius_sq = cell_size ** 2 # 220^2 pre-calculated

        for other in neighbors:
            if other != self:
                dist_vec = self.position - other.position
                d_sq = dist_vec.length_squared()

                if 0 < d_sq < radius_sq:
                    d = math.sqrt(d_sq)
                    # HARD COLLISION
                    if d < 42:
                        nudge = dist_vec.normalize() * (42 - d) * 0.6
                        self.position += nudge
                        # Note: other.position -= nudge is removed here because
                        # 'other' will eventually update itself, preventing double-nudging.

                    sep += dist_vec.normalize() * (cell_size - d)
                    sep = sep/1.5
                    ali += other.velocity
                    coh += other.position
                    neighbor_count += 1

        # 4. BOILING LOGIC
        if neighbor_count > 0:
            if ali.length_squared() > 0:
                ali = ali.normalize() * 1.8

            coh_vec = (coh / neighbor_count) - self.position
            if coh_vec.length_squared() > 0:
                coh = coh_vec.normalize() * 3.5

            t = pygame.time.get_ticks() * 0.002
            pulse = math.sin(t * 0.5 + self.position.x * 0.01) * 3.0
            swirl_force = pygame.Vector2(math.cos(t), math.sin(t)) * (2.0 + pulse)*20

            self.apply_force(sep * 2.2 + ali + coh + swirl_force)

        # 5. TARGETED / HAYWIRE LOGIC
        if is_targeted:
            self.max_speed, self.max_force = 36.0, 6.0
            self.flap_speed = 0.34
            pull_back = pygame.Vector2(0, 0)
            exit_flock = (self.position - flock_center).normalize() * random.randint(200,300)
            to_predator = self.position - predator.position
            flee = to_predator.normalize() * 25.0 if to_predator.length_squared() > 0 else pygame.Vector2(0,0)
            self.apply_force(flee + self.panic_dir + exit_flock)

            # Avoid division by zero if bird is exactly at flock center
            to_center = self.position - flock_center
            if to_center.length_squared() > 0:
                push_out_of_flock = to_center.normalize() * 1000

            # Haywire Zig-Zags
            self.panic_timer -= 1
            if self.panic_timer <= 0:
                self.panic_dir = pygame.Vector2(1, 0).rotate(random.uniform(0, 360)) * 30.0
                self.panic_timer = random.randint(8, 15)

            # Fleeing force
            to_predator = self.position - predator.position
            flee = to_predator.normalize() * 200.0 if to_predator.length_squared() > 0 else pygame.Vector2(0,0)

            # SAFE ZONE TETHER
            dist_sq_to_center = (self.position - flock_center).length_squared()
            safe_zone_sq = 10000 # 80^2 (reduced for tighter control)

            if dist_sq_to_center > safe_zone_sq:
                dist_to_center = math.sqrt(dist_sq_to_center)
                stretch = dist_to_center - 80
                pull_back = (flock_center - self.position).normalize() * (stretch * 0.08)
            else:
                pull_back = pygame.Vector2(0, 0)

            self.apply_force(flee + self.panic_dir + pull_back)

        else:
            # NORMAL BOILING SPEED & SCATTER
            dist_sq_to_predator = (self.position - predator.position).length_squared()
            if dist_sq_to_predator < 22500:
                scatter = (self.position - predator.position).normalize() * 20.0
                self.apply_force(scatter)

            self.max_speed, self.max_force = 14.0, 1.5
            world_center = pygame.Vector2(WIDTH // 2, HEIGHT // 2)

            # Tether to world center
            world_dist_sq = (self.position - world_center).length_squared()
            if world_dist_sq > 160000: # 400^2
                self.apply_force((world_center - self.position).normalize() * 1.2)

        # 6. INTEGRATION (Standard Clamping)
        if self.acceleration.length() > self.max_force:
            self.acceleration.scale_to_length(self.max_force)

        self.velocity += self.acceleration

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.position += self.velocity
        self.acceleration *= 0

        # Determines flapping animation state
        self.is_swooping = is_targeted and self.velocity.length() > 28.0

    def draw(self, screen, falcon_pos, zoom, WIDTH, HEIGHT, is_targeted):
        rel_pos = (self.position - falcon_pos) * zoom + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        if not (-300 < rel_pos.x < WIDTH + 300 and -300 < rel_pos.y < HEIGHT + 300): return

        f = self.velocity.normalize() if self.velocity.length() > 0.1 else self.current_dir
        side = pygame.Vector2(-f.y, f.x)
        s = self.scale * zoom * 0.95 # Keeping the larger size

        # --- COLOR PALETTE ---
        # Real starlings are dark but shimmer with cyan/green
        body_outer = (20, 20, 30)   # Dark near-black edges
        body_inner = (0, 139, 139)  # Cyan iridescent core

        wing_color = (45, 48, 55)
        beak_color = (255, 230, 90)

        # 1. THE TAIL (Sharp Notched V)
        tail_base = rel_pos - f * (8 * s)
        t_l = rel_pos - f * (18 * s) + side * (7 * s)
        t_r = rel_pos - f * (18 * s) - side * (7 * s)
        pygame.draw.polygon(screen, wing_color, [tail_base, t_l, t_r])

        # 2. THE WINGS (Triangular 'Flicker' Flap)
        t = pygame.time.get_ticks() * self.flap_speed
        flap_factor = math.sin(t)
        for i in [1, -1]:
            w_start = rel_pos + f * (2 * s)
            w_tip = rel_pos + f * (8 * s) + (side * 30 * s * flap_factor * i)
            w_back = rel_pos - f * (12 * s) + (side * 5 * s * i)
            pygame.draw.polygon(screen, wing_color, [w_start, w_tip, w_back])

        # 3. SLEEK DIAMOND BODY (Cyan Inner Core)
        # Outer Diamond (Dark outline)
        torso_outer = [
            rel_pos + f * (20 * s),            # Sharp Head
            rel_pos + f * (4 * s) + side * (9 * s),  # Shoulder R
            rel_pos - f * (12 * s),            # Tail Joint
            rel_pos + f * (4 * s) - side * (9 * s)   # Shoulder L
        ]
        pygame.draw.polygon(screen, body_outer, torso_outer)

        # Inner Diamond (Cyan Iridescence)
        # We scale the inner diamond slightly smaller (0.6x) to create an 'outline' effect
        torso_inner = [
            rel_pos + f * (12 * s),
            rel_pos + f * (4 * s) + side * (5 * s),
            rel_pos - f * (6 * s),
            rel_pos + f * (4 * s) - side * (5 * s)
        ]
        pygame.draw.polygon(screen, body_inner, torso_inner)

        # 4. POINTED YELLOW BEAK
        head_tip = rel_pos + f * (20 * s)
        beak_tip = rel_pos + f * (32 * s)
        pygame.draw.polygon(screen, beak_color, [head_tip + side*(1.5*s), beak_tip, head_tip - side*(1.5*s)])

        # 5. EYE
        eye_pos = rel_pos + f * (15 * s) + side * (2.5 * s)
        pygame.draw.circle(screen, (0, 0, 0), (int(eye_pos.x), int(eye_pos.y)), int(1.5 * s))

class PredatorBird:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        cardinal_directions = [
            pygame.Vector2(1, 0),  # Right
            pygame.Vector2(-1, 0), # Left
            pygame.Vector2(0, 1),  # Down
            pygame.Vector2(0, -1)  # Up
        ]

    # Pick exactly one and set the speed
        self.velocity = random.choice(cardinal_directions)*5
        self.acceleration = pygame.Vector2(0, 0)
        self.mass = 50.0
        self.scale = 4.5
        self.current_dir = pygame.Vector2(1, 0)
        self.target_bird = None
        self.chase_time = 0
        self.is_bursting = False
        self.burst_timer = 100
        self.flap_speed = 0.12 / 4

        # --- NEW REALISM VARIABLES ---
        # Frames representing 3s, 5s, 7s, 9s, and 10s at 60fps
        self.returning_to_flock = False

    def apply_force(self, force):
        self.acceleration += force / self.mass

    def update(self, mode, grid, cell_size, flock_center, WIDTH, HEIGHT):
        # 1. ROBUST INITIALIZATION (Identical to your provided code)
        global patrol_target
        if not hasattr(self, 'is_gliding'): self.is_gliding = False
        if not hasattr(self, 'glide_timer'): self.glide_timer = 60
        if not hasattr(self, 'chase_phase'): self.chase_phase = "ORBIT" # Default to Orbit
        if not hasattr(self, 'is_swooping'): self.is_swooping = False
        if not hasattr(self, 'hunt_timer'): self.hunt_timer = 0
        if not hasattr(self, 'patrol_angle'): self.patrol_angle = random.uniform(0, math.pi * 2)

        # 2. TARGET ACQUISITION (Spatial Mapping + Proximity Trigger)
        if mode == "HUNT":
            if not self.target_bird:
                possible_targets = []
                grid_x, grid_y = int(self.position.x // cell_size), int(self.position.y // cell_size)
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        key = (grid_x + dx, grid_y + dy)
                        if key in grid:
                            possible_targets.extend(grid[key])

                if possible_targets:
                    self.target_bird = min(possible_targets, key=lambda b: (b.position - self.position).length_squared())

            # --- THE ATTACK TRIGGER (Now based on Distance to Falcon) ---
            if self.target_bird:
                # Measure distance between falcon and bird (300px threshold = 90000 sq)
                dist_to_falcon_sq = (self.target_bird.position - self.position).length_squared()

                # TRIGGER: Attack if close to falcon (90000) OR manual override (mode is HUNT)
                if dist_to_falcon_sq < 90000:
                    if self.chase_phase == "IDLE" or self.chase_phase == "ORBIT":
                        self.chase_phase = "INTERCEPT"
                        self.hunt_timer = random.randint(300, 600)
                else:
                    # If bird is too far, stay in ORBIT unless you've already started the hunt
                    if self.chase_phase == "ORBIT":
                        self.chase_phase = "ORBIT"
        else:
            self.target_bird = None
            self.hunt_timer = 0
            self.chase_phase = "ORBIT"

        # 3. BEHAVIOR LOGIC
        if mode == "HUNT" and self.target_bird and self.chase_phase != "ORBIT":
            self.hunt_timer -= 1
            dist_vec = self.target_bird.position - self.position
            distance = dist_vec.length()

            if self.chase_phase == "INTERCEPT":
                self.is_swooping = True
                self.max_speed, self.max_force = 60.0, 8.0
                prediction = self.target_bird.velocity * 2
                target_pos = self.target_bird.position + prediction
                target_pos = target_pos/10

                # Crash protection: check distance before normalizing
                if (target_pos - self.position).length_squared() > 0:
                    desired = (target_pos - self.position).normalize() * self.max_speed
                    self.apply_force((desired - self.velocity) * 8.0)

                if distance < 500:
                    self.chase_phase = "TETHERED"

            elif self.chase_phase == "TETHERED":
                # YOUR LATCHING LOGIC
                self.is_swooping = True
                heading = self.target_bird.velocity.normalize() if self.target_bird.velocity.length() > 0 else pygame.Vector2(1,0)
                self.position = self.target_bird.position - (heading * 400) # Snaps closer for the 'catch'
                self.velocity = pygame.Vector2(self.target_bird.velocity)

        else:
            # --- ORBITING PATROL ---
            self.is_swooping = False
            self.chase_phase = "ORBIT"
            self.max_speed, self.max_force = 12.0, 0.4
            self.patrol_angle += 0.05
            orbit_radius = 1800
            orbit_offset = pygame.Vector2(math.cos(self.patrol_angle),
                                          math.sin(self.patrol_angle)) * orbit_radius
            patrol_target = flock_center + orbit_offset

        # 4. SOFT STEERING (Arrive behavior)
        desired = (patrol_target - self.position)
        dist = desired.length()
        if dist > 0:
            desired = desired.normalize() * self.max_speed
            steering = (desired - self.velocity)
            self.apply_force(steering * 0.1)

        # 4. PHYSICS INTEGRATION
        if self.chase_phase != "TETHERED":
            if self.acceleration.length() > self.max_force:
                self.acceleration.scale_to_length(self.max_force)
            self.velocity += self.acceleration
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            self.position += self.velocity

        # 5. GLIDE TIMER
        if not self.is_swooping:
            self.glide_timer -= 1
            if self.glide_timer <= 0:
                self.is_gliding = not self.is_gliding
                self.glide_timer = random.randint(80, 200)
        else:
            self.is_gliding = False

        self.acceleration *= 0

    def draw(self, screen, zoom, WIDTH, HEIGHT):
        center = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        target_dir = self.velocity.normalize() if self.velocity.length() > 0 else self.current_dir
        self.current_dir += (target_dir - self.current_dir) * 0.1
        f = self.current_dir.normalize()
        side = pygame.Vector2(-f.y, f.x)
        s = self.scale * zoom

        WING_COL, BODY_COL, STRIPE_COL = (35, 38, 45), (60, 65, 75), (80, 85, 95)
        BELLY_COL, BEAK_COL = (190, 195, 200), (255, 230, 90)

        # 1. LONGER 'V' TAIL
        # We move the points further back (-35s) and deepen the notch (-20s)
        tail_base = center - f * (15 * s)
        v_left = center - f * (38 * s) + side * (14 * s)
        v_right = center - f * (38 * s) - side * (14 * s)
        v_notch = center - f * (24 * s)
        pygame.draw.polygon(screen, WING_COL, [tail_base, v_left, v_notch, v_right])

        # --- FLAP LOGIC (Kept your original timings) ---
        if self.is_swooping:
            burst_gate = math.sin(pygame.time.get_ticks() * 0.005)
            if burst_gate > 0:
                flap = 0.4 + abs(math.sin(pygame.time.get_ticks()*0.5 * 0.05) * 0.25)
            else:
                flap = 0.5
        elif self.is_gliding:
            flap = 0.9
        else:
            flap = math.sin(pygame.time.get_ticks() * self.flap_speed * 0.3)

        # 2. LONG WINGS WITH SIGNATURE 'V' BEND
        # Changed w_tip and w_elbow to create a sharp, swept-back sickle shape
        for i in [1, -1]:
            w_start = center + f * (8 * s/8)
            # Elbow pushed forward and out to create the 'V' bend
            w_elbow = center + f * (12 * s) + (side * 20 * s * flap * i)
            # Tip stretched back significantly for a long, thin profile
            w_tip = center - f * (25 * s) + (side * 70 * s * flap * i)
            w_back = center - f * (5 * s) + (side * 15 * s * flap * i)

            pygame.draw.polygon(screen, WING_COL, [w_start, w_elbow, w_tip, w_back])

            # Stripes
            for offset in [0.4, 0.7]:
                s_start = w_start + (w_elbow - w_start) * offset
                s_end = w_back + (w_tip - w_back) * offset
                pygame.draw.line(screen, STRIPE_COL, s_start, s_end, int(max(1, 1 * zoom)))

        # 3. TEARDROP BODY
        # Narrowed the tail-end and smoothed the front for a projectile shape
        torso_pts = [
            center + f * (28 * s),           # Front of head
            center + f * (14 * s) + side * (9 * s),  # Broad shoulders
            center - f * (10 * s) + side * (9 * s),  # Tapering flank
            center - f * (22 * s),           # Sharp tail-end point
            center - f * (10 * s) - side * (9 * s),  # Tapering flank
            center + f * (14 * s) - side * (9 * s)   # Broad shoulders
        ]
        pygame.draw.polygon(screen, BODY_COL, torso_pts)

        # Belly detail (Scaled to the teardrop)
        pygame.draw.circle(screen, BELLY_COL, (int(center.x), int(center.y)), int(6.5 * s))

        # 4. REFINED HEAD & SHORT BEAK
        for i in [1, -1]:
            eye_pos = center + f * (20 * s) + side * (4 * s * i)
            pygame.draw.circle(screen, (255, 255, 0), (int(eye_pos.x), int(eye_pos.y)), int(2.2 * s))
            pygame.draw.circle(screen, (0, 0, 0), (int(eye_pos.x), int(eye_pos.y)), int(1.8 * s))

        # Beak is now shorter and more integrated (beak_tip moved from 32s to 28s)
        head_pos = center + f * (26 * s)
        beak_tip = center + f * (33 * s)
        pygame.draw.polygon(screen, BEAK_COL, [head_pos + side * (3 * s), beak_tip, head_pos - side * (3 * s)])