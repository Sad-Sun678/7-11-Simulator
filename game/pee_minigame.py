import pygame
import math
import random

from game.config import PEE_CONFIG


class PeeMinigame:
    """Pee aiming minigame — balance the stream to keep it in the bowl."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Load and scale background
        self.bg = pygame.image.load("assets/background/toilet_bg.png").convert()
        self.bg = pygame.transform.scale(self.bg, (screen_width, screen_height))

        # Bowl hitbox from config
        self.bowl_x = PEE_CONFIG["bowl_x"]
        self.bowl_y = PEE_CONFIG["bowl_y"]
        self.bowl_radius = PEE_CONFIG["bowl_radius"]

        # Pee settings
        self.pee_drain_rate = PEE_CONFIG["pee_drain_rate"]
        self.stream_radius = PEE_CONFIG["stream_radius"]

        # Stream origin: bottom center of screen
        self.origin_x = screen_width // 2
        self.origin_y = screen_height - 30

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.hud_font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 64)

        # State
        self.active = False
        self.bladder_remaining = 0
        self.bladder_start = 0
        self.total_peed = 0
        self.peed_in_bowl = 0

        # Stream endpoint position (only X moves, Y is locked to bowl_y)
        self.stream_x = 0
        self.stream_y = 0

        # Player velocity and acceleration (arrow key physics)
        self.player_vel = 0            # current velocity from player input
        self.player_accel = 800.0      # acceleration per second while key held
        self.player_max_speed = 500.0  # max speed from player input
        self.player_friction = 600.0   # deceleration when no key pressed

        # Random sway force (the "wind" pushing the stream)
        self.sway_vel = 0
        self.sway_force = 0            # current random force
        self.sway_change_timer = 0     # time until next force change
        self.sway_max_force = 450.0    # max sway acceleration (stronger pushes)
        self.sway_change_interval = 0.6  # seconds between force direction changes (more frequent)

        # Splash particles
        self.splash_particles = []
        self.splash_timer = 0

        # Result display
        self.show_result = False
        self.result_timer = 0
        self.result_accuracy = 0

    def start(self, player):
        """Start the minigame with the player's current bladder level."""
        self.bladder_remaining = player.current_bladder
        self.bladder_start = player.current_bladder
        self.total_peed = 0
        self.peed_in_bowl = 0
        self.show_result = False
        self.result_timer = 0
        self.splash_particles = []
        self.splash_timer = 0

        # Start stream at a random X position on the bowl's Y plane
        margin = 150
        self.stream_x = float(random.randint(margin, self.screen_width - margin))
        self.stream_y = float(self.bowl_y)

        # Reset physics
        self.player_vel = 0
        self.sway_vel = 0
        self.sway_force = 0
        self.sway_change_timer = 0

        self.active = True

    def update(self, keys, dt):
        """Update minigame state. Returns result dict when done, None otherwise."""
        if not self.active:
            return None

        # Result screen countdown
        if self.show_result:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.active = False
                return {"accuracy": self.result_accuracy}
            return None

        # --- Random sway (the force that pushes the stream) ---
        self.sway_change_timer -= dt
        if self.sway_change_timer <= 0:
            # Pick a new random sway force direction and strength
            self.sway_force = random.uniform(-self.sway_max_force, self.sway_max_force)
            self.sway_change_timer = random.uniform(0.2, self.sway_change_interval)

        self.sway_vel += self.sway_force * dt
        # Dampen sway so it doesn't go infinite (less dampening = wider swings)
        self.sway_vel *= 0.99

        # --- Player input (arrow keys with acceleration) ---
        input_dir = 0
        if keys[pygame.K_LEFT]:
            input_dir -= 1
        if keys[pygame.K_RIGHT]:
            input_dir += 1

        if input_dir != 0:
            # Accelerate in pressed direction
            self.player_vel += input_dir * self.player_accel * dt
            # Clamp to max speed
            if self.player_vel > self.player_max_speed:
                self.player_vel = self.player_max_speed
            elif self.player_vel < -self.player_max_speed:
                self.player_vel = -self.player_max_speed
        else:
            # Apply friction to slow down when no input
            if self.player_vel > 0:
                self.player_vel -= self.player_friction * dt
                if self.player_vel < 0:
                    self.player_vel = 0
            elif self.player_vel < 0:
                self.player_vel += self.player_friction * dt
                if self.player_vel > 0:
                    self.player_vel = 0

        # --- Apply combined velocity to stream X position ---
        total_vel = self.player_vel + self.sway_vel
        self.stream_x += total_vel * dt

        # Clamp to screen bounds with padding
        margin = 50
        if self.stream_x < margin:
            self.stream_x = margin
            self.player_vel = max(0, self.player_vel)
            self.sway_vel = max(0, self.sway_vel)
        elif self.stream_x > self.screen_width - margin:
            self.stream_x = self.screen_width - margin
            self.player_vel = min(0, self.player_vel)
            self.sway_vel = min(0, self.sway_vel)

        # Y is locked to bowl level
        self.stream_y = float(self.bowl_y)

        # --- Drain bladder and check accuracy ---
        dx = self.stream_x - self.bowl_x
        distance = abs(dx)

        pee_amount = self.pee_drain_rate * dt
        self.total_peed += pee_amount
        self.bladder_remaining -= pee_amount

        # Check if hitting the bowl (for accuracy tracking only)
        if distance <= self.bowl_radius:
            self.peed_in_bowl += pee_amount

        # --- Spawn splash particles at stream endpoint ---
        self.splash_timer -= dt
        if self.splash_timer <= 0:
            self.splash_timer = 0.02  # spawn every 20ms
            ex = int(self.stream_x)
            ey = int(self.stream_y)
            for _ in range(random.randint(1, 3)):
                angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)  # upward arc
                speed = random.uniform(40, 150)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                # Yellow-ish droplet colors
                g = random.randint(200, 240)
                color = (255, g, random.randint(20, 80))
                size = random.uniform(1.5, 3.5)
                life = random.uniform(0.2, 0.5)
                self.splash_particles.append({
                    "x": ex + random.uniform(-4, 4),
                    "y": ey + random.uniform(-4, 4),
                    "vx": vx, "vy": vy,
                    "life": life, "max_life": life,
                    "size": size, "color": color,
                })

        # Update existing splash particles
        alive = []
        for p in self.splash_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 300 * dt  # gravity pulls droplets down
            p["life"] -= dt
            if p["life"] > 0:
                alive.append(p)
        self.splash_particles = alive

        # Check if done
        if self.bladder_remaining <= 0:
            self.bladder_remaining = 0
            if self.total_peed > 0:
                self.result_accuracy = (self.peed_in_bowl / self.total_peed) * 100
            else:
                self.result_accuracy = 0
            self.show_result = True
            self.result_timer = 2.5

        return None

    def cancel(self):
        """Cancel the minigame without finishing."""
        self.active = False

    def draw(self, screen):
        """Draw the minigame screen."""
        # Background
        screen.blit(self.bg, (0, 0))

        if self.show_result:
            self._draw_result(screen)
            return

        # Bowl hitbox (semi-transparent circle so user can see/position it)
        bowl_surface = pygame.Surface(
            (self.bowl_radius * 2, self.bowl_radius * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            bowl_surface, (100, 180, 255, 50),
            (self.bowl_radius, self.bowl_radius), self.bowl_radius
        )
        pygame.draw.circle(
            bowl_surface, (100, 180, 255, 120),
            (self.bowl_radius, self.bowl_radius), self.bowl_radius, 2
        )
        screen.blit(bowl_surface,
                     (self.bowl_x - self.bowl_radius, self.bowl_y - self.bowl_radius))

        # --- Draw pee stream arc from origin to endpoint ---
        self._draw_stream(screen)

        # Pee stream endpoint (main circle)
        end_x = int(self.stream_x)
        end_y = int(self.stream_y)
        pygame.draw.circle(screen, (255, 230, 50), (end_x, end_y), self.stream_radius)
        pygame.draw.circle(screen, (220, 200, 30), (end_x, end_y), self.stream_radius, 2)

        # Splash particles
        for p in self.splash_particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            sz = max(1, int(p["size"] * (p["life"] / p["max_life"])))
            surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            color_a = (*p["color"], alpha)
            pygame.draw.circle(surf, color_a, (sz, sz), sz)
            screen.blit(surf, (int(p["x"]) - sz, int(p["y"]) - sz))

        # Bladder meter bar at top
        self._draw_bladder_bar(screen)

        # Accuracy display
        if self.total_peed > 0:
            accuracy = (self.peed_in_bowl / self.total_peed) * 100
        else:
            accuracy = 0
        acc_text = self.hud_font.render(f"Accuracy: {accuracy:.0f}%", True, (255, 255, 255))
        acc_shadow = self.hud_font.render(f"Accuracy: {accuracy:.0f}%", True, (0, 0, 0))
        screen.blit(acc_shadow, (self.screen_width // 2 - acc_text.get_width() // 2 + 2, 52))
        screen.blit(acc_text, (self.screen_width // 2 - acc_text.get_width() // 2, 50))

        # Title
        title = self.title_font.render("KEEP IT IN THE BOWL!", True, (255, 255, 200))
        title_shadow = self.title_font.render("KEEP IT IN THE BOWL!", True, (0, 0, 0))
        screen.blit(title_shadow, (self.screen_width // 2 - title.get_width() // 2 + 2, 12))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 10))

        # Arrow key hint
        hint = self.hud_font.render("< LEFT / RIGHT >", True, (200, 200, 200))
        screen.blit(hint, (self.screen_width // 2 - hint.get_width() // 2,
                           self.screen_height - 40))

    def _draw_stream(self, screen):
        """Draw a curved pee stream from origin (bottom center) to endpoint."""
        end_x = int(self.stream_x)
        end_y = int(self.stream_y)
        ox = self.origin_x
        oy = self.origin_y

        # Use a quadratic bezier curve
        # Control point: midpoint X between origin and end, raised above both
        mid_x = (ox + end_x) / 2
        mid_y = min(oy, end_y) - 150  # Arc peaks 150px above the lower point

        segments = 20
        prev_point = None
        for i in range(segments + 1):
            t = i / segments
            # Quadratic bezier: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            inv_t = 1 - t
            bx = inv_t * inv_t * ox + 2 * inv_t * t * mid_x + t * t * end_x
            by = inv_t * inv_t * oy + 2 * inv_t * t * mid_y + t * t * end_y

            point = (int(bx), int(by))

            if prev_point is not None:
                # Thickness tapers from thick at origin to thin at end
                thickness = max(2, int(6 * (1 - t) + 2))
                # Color gets slightly more transparent toward the end
                alpha = int(200 + 55 * (1 - t))
                pygame.draw.line(screen, (255, 230, 50), prev_point, point, thickness)

            prev_point = point

    def _draw_bladder_bar(self, screen):
        """Draw the bladder meter bar at top of screen."""
        bar_width = 300
        bar_height = 20
        bar_x = self.screen_width // 2 - bar_width // 2
        bar_y = 80

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=8)

        # Fill
        if self.bladder_start > 0:
            pct = max(0, self.bladder_remaining / self.bladder_start)
        else:
            pct = 0
        fill_w = int(bar_width * pct)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_height)
            pygame.draw.rect(screen, (100, 180, 255), fill_rect, border_radius=8)

        # Border
        pygame.draw.rect(screen, (80, 80, 80), bg_rect, 2, border_radius=8)

        # Label
        label = self.hud_font.render("Bladder", True, (200, 200, 200))
        screen.blit(label, (bar_x - label.get_width() - 10, bar_y - 2))

    def _draw_result(self, screen):
        """Draw the result screen overlay."""
        # Semi-transparent dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Result text
        acc_text = self.big_font.render(f"{self.result_accuracy:.0f}% Accuracy!", True, (255, 255, 100))
        screen.blit(acc_text,
                     (self.screen_width // 2 - acc_text.get_width() // 2,
                      self.screen_height // 2 - 60))

        xp = int(self.result_accuracy * PEE_CONFIG["xp_per_accuracy_point"])
        xp_text = self.title_font.render(f"+{xp} XP", True, (100, 255, 100))
        screen.blit(xp_text,
                     (self.screen_width // 2 - xp_text.get_width() // 2,
                      self.screen_height // 2 + 20))

        relief = self.hud_font.render("Ahhhh, sweet relief!", True, (200, 200, 255))
        screen.blit(relief,
                     (self.screen_width // 2 - relief.get_width() // 2,
                      self.screen_height // 2 + 80))
