import pygame
import random
import math

from game.config import SYMBOLS, SYMBOL_IMAGES, TICKET_TYPES


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


class Match3Ticket:
    """A scratch ticket where you need to match 3 symbols to win."""

    # Fixed size for Match 3 tickets - larger to fit symbols properly
    TICKET_WIDTH = 340
    TICKET_HEIGHT = 280

    # Grid layout constants
    GRID_PADDING = 20  # Padding around the grid
    HEADER_HEIGHT = 45  # Space for title
    FOOTER_HEIGHT = 30  # Space for prize text
    CELL_PADDING = 8  # Padding between cells

    def __init__(self, ticket_type, x, y, width=340, height=280, luck_bonus=0):
        self.ticket_type = ticket_type
        self.config = TICKET_TYPES[ticket_type]
        self.x = x
        self.y = y
        # Use fixed size for Match 3 tickets to ensure proper spacing
        self.width = self.TICKET_WIDTH
        self.height = self.TICKET_HEIGHT
        self.luck_bonus = luck_bonus

        # Generate symbols for the 9 spots (3x3 grid)
        self.symbols = self._generate_symbols()
        self.prize = self._calculate_prize()

        # Calculate cell positions and sizes
        self._calculate_grid_layout()

        # Track which cells have been revealed (for completion check)
        self.cells_revealed = [False] * 9

        # Create surfaces
        self._create_surfaces()

        # Scratch tracking
        self.scratched = False
        self.scratch_percent = 0
        self.revealed = False

    def _calculate_grid_layout(self):
        """Calculate the grid layout with proper spacing."""
        # Available space for the grid
        grid_width = self.width - (self.GRID_PADDING * 2)
        grid_height = self.height - self.HEADER_HEIGHT - self.FOOTER_HEIGHT - self.GRID_PADDING

        # Cell size (square cells with padding)
        self.cell_size = min(grid_width // 3, grid_height // 3) - self.CELL_PADDING

        # Actual grid dimensions
        actual_grid_width = (self.cell_size * 3) + (self.CELL_PADDING * 2)
        actual_grid_height = (self.cell_size * 3) + (self.CELL_PADDING * 2)

        # Grid starting position (centered)
        self.grid_start_x = (self.width - actual_grid_width) // 2
        self.grid_start_y = self.HEADER_HEIGHT + (grid_height - actual_grid_height) // 2

        # Store cell centers and bounds for hit detection
        self.cell_centers = []
        self.cell_bounds = []

        for i in range(9):
            row = i // 3
            col = i % 3

            cx = self.grid_start_x + col * (self.cell_size + self.CELL_PADDING) + self.cell_size // 2
            cy = self.grid_start_y + row * (self.cell_size + self.CELL_PADDING) + self.cell_size // 2

            self.cell_centers.append((cx, cy))

            # Cell bounds for hit detection (slightly smaller than visual)
            cell_left = cx - self.cell_size // 2
            cell_top = cy - self.cell_size // 2
            self.cell_bounds.append(pygame.Rect(cell_left, cell_top, self.cell_size, self.cell_size))

    def _generate_symbols(self):
        """Generate 9 symbols for the grid. Luck bonus increases match chance."""
        available = self.config["symbols"]
        symbols = []

        # Determine if we should force a match (based on luck)
        match_chance = 0.3 + (self.luck_bonus * 0.05)  # 30% base + 5% per luck level

        if random.random() < match_chance:
            # Force at least one match of 3
            winning_symbol = random.choice(available)
            # Place 3 matching symbols
            symbols = [winning_symbol] * 3
            # Fill rest randomly
            for _ in range(6):
                symbols.append(random.choice(available))
            random.shuffle(symbols)
        else:
            # Random symbols (might still match by chance)
            for _ in range(9):
                symbols.append(random.choice(available))

        return symbols

    def _calculate_prize(self):
        """Calculate prize based on matched symbols."""
        # Count occurrences of each symbol
        counts = {}
        for sym in self.symbols:
            counts[sym] = counts.get(sym, 0) + 1

        # Find best match (3 or more of same symbol)
        best_prize = 0
        self.winning_symbol = None
        self.winning_positions = []

        for sym, count in counts.items():
            if count >= 3:
                symbol_value = SYMBOLS[sym]["value"]
                # Bonus for more than 3 matches
                multiplier = 1 + (count - 3) * 0.5  # 4 matches = 1.5x, 5 = 2x, etc
                prize = int(symbol_value * multiplier)
                if prize > best_prize:
                    best_prize = prize
                    self.winning_symbol = sym
                    # Find ALL positions of winning symbols (not just 3)
                    self.winning_positions = [i for i, s in enumerate(self.symbols) if s == sym]

        return best_prize

    def _create_surfaces(self):
        """Create the ticket surfaces."""
        # Base ticket surface
        self.base_surface = pygame.Surface((self.width, self.height))
        self.base_surface.fill(self.config["color"])

        # Draw ticket border
        pygame.draw.rect(self.base_surface, (255, 255, 255),
                        (0, 0, self.width, self.height), 4, border_radius=12)

        # Draw ticket name at top
        font = pygame.font.Font(None, 32)
        name_text = font.render(self.config["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(centerx=self.width//2, y=10)
        self.base_surface.blit(name_text, name_rect)

        # Draw "Match 3 to Win!" subtitle
        small_font = pygame.font.Font(None, 22)
        subtitle = small_font.render("Match 3 to Win!", True, (255, 255, 200))
        self.base_surface.blit(subtitle, (self.width//2 - subtitle.get_width()//2, 32))

        # Draw grid background
        grid_bg_rect = pygame.Rect(
            self.grid_start_x - 10,
            self.grid_start_y - 10,
            (self.cell_size * 3) + (self.CELL_PADDING * 2) + 20,
            (self.cell_size * 3) + (self.CELL_PADDING * 2) + 20
        )
        pygame.draw.rect(self.base_surface, (255, 255, 240), grid_bg_rect, border_radius=10)
        pygame.draw.rect(self.base_surface, (200, 180, 100), grid_bg_rect, 3, border_radius=10)

        # Draw the 3x3 grid of symbols with proper spacing
        for i, sym in enumerate(self.symbols):
            cx, cy = self.cell_centers[i]
            is_winner = i in self.winning_positions
            self._draw_symbol(cx, cy, sym, self.cell_size, is_winner)

        # Draw prize info at bottom if winner
        if self.prize > 0:
            prize_font = pygame.font.Font(None, 28)
            prize_text = prize_font.render(f"WIN ${self.prize}!", True, (50, 180, 50))
            self.base_surface.blit(prize_text,
                (self.width//2 - prize_text.get_width()//2, self.height - 28))

        # Scratch layer
        self.scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.scratch_surface.fill((*self.config["scratch_color"], 255))

        # Draw "SCRATCH TO REVEAL!" text
        scratch_font = pygame.font.Font(None, 26)
        scratch_text = scratch_font.render("SCRATCH TO REVEAL!", True, (100, 100, 100))
        self.scratch_surface.blit(scratch_text,
            (self.width//2 - scratch_text.get_width()//2, 10))

        # Draw ? marks for each cell in their own boxes
        q_font = pygame.font.Font(None, int(self.cell_size * 0.6))
        for i in range(9):
            cx, cy = self.cell_centers[i]

            # Draw cell outline on scratch surface
            cell_rect = pygame.Rect(
                cx - self.cell_size // 2 + 2,
                cy - self.cell_size // 2 + 2,
                self.cell_size - 4,
                self.cell_size - 4
            )
            pygame.draw.rect(self.scratch_surface, (150, 130, 150, 255), cell_rect, border_radius=8)
            pygame.draw.rect(self.scratch_surface, (120, 100, 120, 255), cell_rect, 2, border_radius=8)

            # Draw ? in center
            q_text = q_font.render("?", True, (80, 60, 80))
            self.scratch_surface.blit(q_text, (cx - q_text.get_width()//2, cy - q_text.get_height()//2))

        # Add subtle texture
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            color = tuple(c + random.randint(-10, 10) for c in self.config["scratch_color"])
            color = tuple(max(0, min(255, c)) for c in color)
            pygame.draw.circle(self.scratch_surface, (*color, 255), (x, y), random.randint(1, 4))

    def _draw_symbol(self, cx, cy, symbol_name, cell_size, is_winner=False):
        """Draw a symbol using sprite images instead of procedural shapes."""

        # Keep winner highlight exactly as before
        if is_winner:
            pygame.draw.rect(self.base_surface, (255, 255, 150),
                             (cx - cell_size // 2 + 2, cy - cell_size // 2 + 2, cell_size - 4, cell_size - 4),
                             border_radius=8)

        # Keep cell background exactly as before
        pygame.draw.rect(self.base_surface, (255, 255, 255),
                         (cx - cell_size // 2 + 4, cy - cell_size // 2 + 4, cell_size - 8, cell_size - 8),
                         border_radius=6)
        pygame.draw.rect(self.base_surface, (200, 200, 200),
                         (cx - cell_size // 2 + 4, cy - cell_size // 2 + 4, cell_size - 8, cell_size - 8),
                         2, border_radius=6)

        # --- NEW PART: sprite drawing ---

        img = SYMBOL_IMAGES[symbol_name]

        scaled = pygame.transform.scale(img, (cell_size - 16, cell_size - 16))
        rect = scaled.get_rect(center=(cx, cy))

        self.base_surface.blit(scaled, rect)

    def _draw_star_symbol(self, x, y, size, color):
        """Draw a star shape."""
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            points.append((x + math.cos(angle) * size, y + math.sin(angle) * size))
            angle = math.radians(i * 72 - 90 + 36)
            points.append((x + math.cos(angle) * size * 0.4, y + math.sin(angle) * size * 0.4))
        pygame.draw.polygon(self.base_surface, color, points)

    def scratch(self, mouse_x, mouse_y, radius=20):
        """Scratch at the given position."""
        local_x = mouse_x - self.x
        local_y = mouse_y - self.y

        if 0 <= local_x < self.width and 0 <= local_y < self.height:
            pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (local_x, local_y), radius)

            for _ in range(3):
                offset_x = local_x + random.randint(-radius//2, radius//2)
                offset_y = local_y + random.randint(-radius//2, radius//2)
                small_radius = random.randint(radius//3, radius//2)
                pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (offset_x, offset_y), small_radius)

            self.scratched = True
            self._update_cells_revealed()

            return {
                "x": mouse_x,
                "y": mouse_y,
                "color": self.config["scratch_color"]
            }
        return None

    def _update_cells_revealed(self):
        """Check which cells have been sufficiently scratched to reveal the symbol."""
        for i in range(9):
            if self.cells_revealed[i]:
                continue  # Already revealed

            cx, cy = self.cell_centers[i]
            # Sample points within this cell to check if it's revealed
            sample_count = 12
            revealed_count = 0

            # Sample in a grid pattern within the cell
            for sx in range(-1, 2):
                for sy in range(-1, 2):
                    sample_x = cx + sx * (self.cell_size // 4)
                    sample_y = cy + sy * (self.cell_size // 4)

                    if 0 <= sample_x < self.width and 0 <= sample_y < self.height:
                        pixel = self.scratch_surface.get_at((sample_x, sample_y))
                        if pixel[3] < 128:  # Transparent = scratched
                            revealed_count += 1

            # Cell is revealed if most of it is scratched (at least 6 of 9 sample points)
            if revealed_count >= 6:
                self.cells_revealed[i] = True

        # Update revealed flag
        if all(self.cells_revealed) and not self.revealed:
            self.revealed = True

    def is_complete(self):
        """Ticket is complete when all 9 cells have been revealed."""
        return all(self.cells_revealed)

    def get_cells_revealed_count(self):
        """Get the number of cells revealed (for progress display)."""
        return sum(self.cells_revealed)

    def get_prize(self):
        return self.prize

    def draw(self, screen):
        screen.blit(self.base_surface, (self.x, self.y))
        screen.blit(self.scratch_surface, (self.x, self.y))
        pygame.draw.rect(screen, (80, 60, 40),
                        (self.x - 2, self.y - 2, self.width + 4, self.height + 4),
                        4, border_radius=12)

        # Draw progress indicator (cells revealed)
        revealed = self.get_cells_revealed_count()
        if revealed < 9 and self.scratched:
            font = pygame.font.Font(None, 20)
            progress_text = font.render(f"{revealed}/9 revealed", True, (200, 200, 200))
            screen.blit(progress_text,
                (self.x + self.width//2 - progress_text.get_width()//2, self.y + self.height + 5))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


def create_ticket(ticket_type, x, y, width=300, height=200, luck_bonus=0):
    """Factory function to create the right ticket type."""
    config = TICKET_TYPES[ticket_type]
    ticket_class = config.get("ticket_class", "standard")

    if ticket_class == "match3":
        # Match3 tickets use their own fixed size for proper symbol spacing
        return Match3Ticket(ticket_type, x, y, luck_bonus=luck_bonus)
    else:
        return ScratchTicket(ticket_type, x, y, width, height, luck_bonus)
