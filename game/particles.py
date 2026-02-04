import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, velocity, lifetime=1.0, size=4, gravity=0):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity
        self.alpha = 255

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt

        # Fade out
        if self.lifetime < self.max_lifetime * 0.5:
            self.alpha = int(255 * (self.lifetime / (self.max_lifetime * 0.5)))

        return self.lifetime > 0

    def draw(self, screen):
        if self.alpha <= 0:
            return

        # Create a surface for the particle with alpha
        surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(surf, color_with_alpha, (self.size, self.size), self.size)
        screen.blit(surf, (self.x - self.size, self.y - self.size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_scratch_particles(self, x, y, color, count=5):
        """Add particles for scratching effect."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Vary the color slightly
            varied_color = tuple(
                max(0, min(255, c + random.randint(-30, 30)))
                for c in color
            )

            particle = Particle(
                x, y, varied_color,
                (vx, vy),
                lifetime=random.uniform(0.3, 0.6),
                size=random.randint(2, 4),
                gravity=100
            )
            self.particles.append(particle)

    def add_win_particles(self, x, y, amount, count=30):
        """Add celebratory particles for winning."""
        # Gold/yellow particles
        colors = [
            (255, 215, 0),   # Gold
            (255, 255, 100), # Yellow
            (100, 255, 100), # Green (money)
            (255, 255, 255), # White sparkle
        ]

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 100  # Bias upward

            color = random.choice(colors)

            particle = Particle(
                x, y, color,
                (vx, vy),
                lifetime=random.uniform(1.0, 2.0),
                size=random.randint(3, 8),
                gravity=200
            )
            self.particles.append(particle)

    def add_big_win_particles(self, x, y, amount, count=80):
        """Add extra celebratory particles for big wins."""
        self.add_win_particles(x, y, amount, count)

        # Add some star-shaped bursts
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(50, 150)
            px = x + math.cos(angle) * dist
            py = y + math.sin(angle) * dist
            self.add_win_particles(px, py, amount, 10)

    def add_coin_trail(self, x, y):
        """Add a trail of coin-like particles."""
        colors = [(255, 215, 0), (255, 200, 50), (200, 180, 50)]
        color = random.choice(colors)

        particle = Particle(
            x + random.randint(-5, 5),
            y + random.randint(-5, 5),
            color,
            (random.uniform(-20, 20), random.uniform(-50, -100)),
            lifetime=0.5,
            size=random.randint(2, 4),
            gravity=300
        )
        self.particles.append(particle)

    def update(self, dt):
        """Update all particles."""
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, screen):
        """Draw all particles."""
        for particle in self.particles:
            particle.draw(screen)

    def clear(self):
        """Clear all particles."""
        self.particles = []


class ScreenShake:
    def __init__(self):
        self.shake_amount = 0
        self.shake_duration = 0
        self.offset_x = 0
        self.offset_y = 0

    def shake(self, amount, duration=0.3):
        """Start a screen shake effect."""
        self.shake_amount = amount
        self.shake_duration = duration

    def update(self, dt):
        """Update shake effect."""
        if self.shake_duration > 0:
            self.shake_duration -= dt
            intensity = self.shake_amount * (self.shake_duration / 0.3)
            self.offset_x = random.uniform(-intensity, intensity)
            self.offset_y = random.uniform(-intensity, intensity)
        else:
            self.offset_x = 0
            self.offset_y = 0

    def get_offset(self):
        """Get the current shake offset."""
        return (int(self.offset_x), int(self.offset_y))
