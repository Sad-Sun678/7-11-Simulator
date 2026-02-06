import pygame
import math
import random
from collections import deque


class DrunkEffect:
    def __init__(self):
        self.time = 0.0
        self.enabled = False

        # Sway
        self.sway_strength_x = 50
        self.sway_strength_y = 20
        self.speed = 0.7
        self.noise = 0.5

        # Double vision
        self.ghost_delay = 0.5  # seconds
        self._offset_history = deque()  # holds (time, (x,y))
        self.double_vision_strength = 50  # pixels
        self.double_vision_alpha = 220  # Transparency
        self.ghost_trails = {}
        self.ghost_cache = {}

        self.smear_count = 3  # how many smear copies
        self.smear_spacing = 1.2  # how far apart they feel

        self.ghost_lag = 20.0  # higher = slower catch-up

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.time = 0.0

    def update(self, dt):
        if not self.enabled:
            self._offset_history.clear()
            return

        self.time += dt * self.speed

        # record the "camera" offset for delayed ghosting
        cur_offset = self.get_offset()
        self._offset_history.append((self.time, cur_offset))

        # drop history older than we need (keep a bit extra)
        cutoff = self.time - (self.ghost_delay + 0.5)
        while self._offset_history and self._offset_history[0][0] < cutoff:
            self._offset_history.popleft()

    def get_offset(self):
        if not self.enabled:
            return (0, 0)

        x = math.sin(self.time) * self.sway_strength_x
        y = math.cos(self.time * 0.7) * self.sway_strength_y

        x += random.uniform(-self.noise, self.noise)
        y += random.uniform(-self.noise, self.noise)

        return int(x), int(y)

    def get_ticket_offset(self):
        if not self.enabled:
            return (0, 0)

        t = self.time

        x = math.sin(t * 1.3 + 2.0) * (self.sway_strength_x * 0.4)
        y = math.cos(t * 1.1 + 1.0) * (self.sway_strength_y * 0.4)

        x += math.sin(t * 2.7) * 4
        y += math.cos(t * 2.3) * 4

        return int(x), int(y)

    # ---------------- DOUBLE VISION ----------------
    def draw_double(self, screen, surface, real_offset, key):
        if not self.enabled:
            screen.blit(surface, real_offset)
            return

        if key not in self.ghost_trails:
            self.ghost_trails[key] = []

        trail = self.ghost_trails[key]

        if not trail:
            trail.append(real_offset)
        else:
            last_x, last_y = trail[0]

            smooth = 0.35  # lower = smoother (0.2-0.4 good)

            smoothed = (
                last_x + (real_offset[0] - last_x) * smooth,
                last_y + (real_offset[1] - last_y) * smooth
            )

            trail.insert(0, smoothed)
        if len(trail) > self.smear_count + 1:
            trail.pop()

        # Build ghost cache ONCE per surface
        if key not in self.ghost_cache:
            ghost = surface.copy().convert_alpha()
            ghost.fill((200, 200, 200), special_flags=pygame.BLEND_RGB_MULT)
            self.ghost_cache[key] = ghost

        ghost_surface = self.ghost_cache[key]

        # Draw smear
        for i in range(len(trail) - 1, 0, -1):
            t = i / len(trail)
            alpha = int(self.double_vision_alpha * (1 - t))

            bx = math.sin(self.time * 1.6 + i) * 2
            by = math.cos(self.time * 1.3 + i) * 2

            ghost_surface.set_alpha(alpha)

            spread = 1 + i * 0.6
            screen.blit(
                ghost_surface,
                (
                    real_offset[0] + (trail[i][0] - real_offset[0]) * spread + bx,
                    real_offset[1] + (trail[i][1] - real_offset[1]) * spread + by
                )
            )

        screen.blit(surface, real_offset)
