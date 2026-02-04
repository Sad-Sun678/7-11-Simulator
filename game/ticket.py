import pygame
import random
import math

# Ticket type definitions
TICKET_TYPES = {
    "basic": {
        "name": "Basic",
        "cost": 1,
        "color": (100, 180, 100),  # Green
        "scratch_color": (180, 180, 180),  # Gray
        "prizes": [0, 0, 0, 0, 0, 1, 1, 2, 5, 10],  # Weighted prizes
        "unlock_threshold": 0,
    },
    "lucky7": {
        "name": "Lucky 7s",
        "cost": 5,
        "color": (180, 100, 180),  # Purple
        "scratch_color": (200, 180, 200),
        "prizes": [0, 0, 0, 0, 7, 7, 14, 21, 49, 77],
        "unlock_threshold": 50,
    },
    "bigmoney": {
        "name": "Big Money",
        "cost": 10,
        "color": (100, 150, 200),  # Blue
        "scratch_color": (180, 200, 220),
        "prizes": [0, 0, 0, 0, 0, 10, 25, 50, 100, 500],
        "unlock_threshold": 200,
    },
    "jackpot": {
        "name": "Jackpot",
        "cost": 25,
        "color": (220, 180, 80),  # Gold
        "scratch_color": (240, 220, 180),
        "prizes": [0, 0, 0, 0, 0, 0, 50, 100, 500, 5000],
        "unlock_threshold": 1000,
    },
}


class ScratchTicket:
    def __init__(self, ticket_type, x, y, width=300, height=200, luck_bonus=0):
        self.ticket_type = ticket_type
        self.config = TICKET_TYPES[ticket_type]
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.luck_bonus = luck_bonus

        # Generate the prize
        self.prize = self._generate_prize()

        # Create surfaces
        self._create_surfaces()

        # Scratch tracking
        self.scratched = False
        self.scratch_percent = 0
        self.revealed = False
        self.total_pixels = 0
        self.scratched_pixels = 0

    def _generate_prize(self):
        prizes = self.config["prizes"]
        # Luck bonus shifts towards better prizes
        index = random.randint(0, len(prizes) - 1)
        # Apply luck bonus - chance to reroll for better
        for _ in range(self.luck_bonus):
            new_index = random.randint(0, len(prizes) - 1)
            if new_index > index:
                index = new_index
        return prizes[index]

    def _create_surfaces(self):
        # Base ticket surface (what's underneath)
        self.base_surface = pygame.Surface((self.width, self.height))
        self.base_surface.fill(self.config["color"])

        # Draw ticket border and design
        pygame.draw.rect(self.base_surface, (255, 255, 255),
                        (0, 0, self.width, self.height), 4, border_radius=10)

        # Draw ticket name at top
        font = pygame.font.Font(None, 28)
        name_text = font.render(self.config["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(centerx=self.width//2, y=10)
        self.base_surface.blit(name_text, name_rect)

        # Draw prize reveal area
        prize_area = pygame.Rect(30, 50, self.width - 60, self.height - 80)
        pygame.draw.rect(self.base_surface, (255, 255, 240), prize_area, border_radius=8)
        pygame.draw.rect(self.base_surface, (200, 180, 100), prize_area, 3, border_radius=8)

        # Draw prize amount
        prize_font = pygame.font.Font(None, 64)
        if self.prize > 0:
            prize_text = prize_font.render(f"${self.prize}", True, (50, 150, 50))
        else:
            prize_text = prize_font.render("SORRY!", True, (180, 80, 80))
        prize_rect = prize_text.get_rect(center=(self.width//2, self.height//2 + 10))
        self.base_surface.blit(prize_text, prize_rect)

        # Draw decorative symbols
        self._draw_decorations()

        # Scratch layer (gray covering)
        self.scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.scratch_surface.fill((*self.config["scratch_color"], 255))

        # Draw "SCRATCH HERE" text on scratch layer
        scratch_font = pygame.font.Font(None, 36)
        scratch_text = scratch_font.render("SCRATCH HERE!", True, (100, 100, 100))
        scratch_rect = scratch_text.get_rect(center=(self.width//2, self.height//2))
        self.scratch_surface.blit(scratch_text, scratch_rect)

        # Add some texture to scratch surface
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            color = tuple(c + random.randint(-20, 20) for c in self.config["scratch_color"])
            color = tuple(max(0, min(255, c)) for c in color)
            pygame.draw.circle(self.scratch_surface, (*color, 255), (x, y), random.randint(2, 8))

        # Calculate total scratchable pixels
        self.total_pixels = self.width * self.height

    def _draw_decorations(self):
        # Draw stars or symbols around the prize
        for i in range(4):
            angle = i * 90 + 45
            x = self.width // 2 + int(math.cos(math.radians(angle)) * 80)
            y = self.height // 2 + 10 + int(math.sin(math.radians(angle)) * 50)
            self._draw_star(x, y, 12, (255, 220, 100))

    def _draw_star(self, x, y, size, color):
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            points.append((x + math.cos(angle) * size, y + math.sin(angle) * size))
            angle = math.radians(i * 72 - 90 + 36)
            points.append((x + math.cos(angle) * size * 0.4, y + math.sin(angle) * size * 0.4))
        pygame.draw.polygon(self.base_surface, color, points)

    def scratch(self, mouse_x, mouse_y, radius=20):
        """Scratch at the given position. Returns particles for effects."""
        # Convert to local coordinates
        local_x = mouse_x - self.x
        local_y = mouse_y - self.y

        # Check if within ticket bounds
        if 0 <= local_x < self.width and 0 <= local_y < self.height:
            # Remove scratch material (make transparent)
            pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (local_x, local_y), radius)

            # Add some texture to the scratch edge
            for _ in range(3):
                offset_x = local_x + random.randint(-radius//2, radius//2)
                offset_y = local_y + random.randint(-radius//2, radius//2)
                small_radius = random.randint(radius//3, radius//2)
                pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (offset_x, offset_y), small_radius)

            self.scratched = True
            self._update_scratch_percent()

            # Return scratch particle info
            return {
                "x": mouse_x,
                "y": mouse_y,
                "color": self.config["scratch_color"]
            }
        return None

    def _update_scratch_percent(self):
        """Calculate how much of the ticket has been scratched."""
        # Sample the scratch surface to estimate scratched area
        # This is an approximation for performance
        sample_points = 100
        transparent_count = 0

        for _ in range(sample_points):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pixel = self.scratch_surface.get_at((x, y))
            if pixel[3] < 128:  # Alpha less than half = scratched
                transparent_count += 1

        self.scratch_percent = transparent_count / sample_points

        # Auto-reveal if scratched enough
        if self.scratch_percent >= 0.5 and not self.revealed:
            self.revealed = True

    def is_complete(self):
        """Check if ticket is sufficiently scratched."""
        return self.scratch_percent >= 0.5

    def get_prize(self):
        """Get the prize amount."""
        return self.prize

    def draw(self, screen):
        """Draw the ticket on the screen."""
        # Draw base (prize underneath)
        screen.blit(self.base_surface, (self.x, self.y))

        # Draw scratch layer on top
        screen.blit(self.scratch_surface, (self.x, self.y))

        # Draw outer border
        pygame.draw.rect(screen, (80, 60, 40),
                        (self.x - 2, self.y - 2, self.width + 4, self.height + 4),
                        4, border_radius=12)

    def get_rect(self):
        """Get the ticket's bounding rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
