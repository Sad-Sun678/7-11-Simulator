import pygame
import random
import math

from game.config import SYMBOLS, SYMBOL_IMAGES, TICKET_TYPES, TICKET_IMAGES


class ScratchTicket:
    def __init__(self, ticket_type, x, y, width=300, height=200, luck_bonus=0):
        self.ticket_type = ticket_type
        self.config = TICKET_TYPES[ticket_type]
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.luck_bonus = luck_bonus

        # Drag handle
        self.handle_height = 28
        self.dragging = False
        self.drag_offset = (0, 0)

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
        # Base ticket surface (custom PNG or fallback procedural)
        self.base_surface = pygame.Surface((self.width, self.height))
        has_custom_base = False

        base_img_name = self.config.get("base_image")
        if base_img_name and base_img_name in TICKET_IMAGES:
            scaled = pygame.transform.scale(TICKET_IMAGES[base_img_name],
                                            (self.width, self.height))
            self.base_surface.blit(scaled, (0, 0))
            has_custom_base = True
        else:
            self.base_surface.fill(self.config["color"])

            # Draw ticket border and design
            pygame.draw.rect(self.base_surface, (255, 255, 255),
                            (0, 0, self.width, self.height), 4, border_radius=10)

            # Draw ticket name at top
            font = pygame.font.Font(None, 28)
            name_text = font.render(self.config["name"], True, (255, 255, 255))
            name_rect = name_text.get_rect(centerx=self.width//2, y=10)
            self.base_surface.blit(name_text, name_rect)

        # Skip decorative chrome when using custom base art — your PNG handles that
        if not has_custom_base:
            prize_area = pygame.Rect(30, 50, self.width - 60, self.height - 80)
            pygame.draw.rect(self.base_surface, (255, 255, 240), prize_area, border_radius=8)
            pygame.draw.rect(self.base_surface, (200, 180, 100), prize_area, 3, border_radius=8)

        # Draw prize amount (always — this is dynamic game data)
        prize_font = pygame.font.Font(None, 64)
        if self.prize > 0:
            prize_text = prize_font.render(f"${self.prize}", True, (50, 150, 50))
        else:
            prize_text = prize_font.render("SORRY!", True, (180, 80, 80))
        prize_rect = prize_text.get_rect(center=(self.width//2, self.height//2 + 10))
        self.base_surface.blit(prize_text, prize_rect)

        # Draw decorative symbols (skip with custom art)
        if not has_custom_base:
            self._draw_decorations()

        # Scratch layer (custom PNG or fallback solid color)
        self.scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        scratch_img_name = self.config.get("scratch_image")
        if scratch_img_name and scratch_img_name in TICKET_IMAGES:
            # Use custom pixel-art cover scaled to ticket size
            scaled = pygame.transform.scale(TICKET_IMAGES[scratch_img_name],
                                            (self.width, self.height))
            self.scratch_surface.blit(scaled, (0, 0))
        else:
            # Fallback: solid scratch color with texture
            self.scratch_surface.fill((*self.config["scratch_color"], 255))

            scratch_font = pygame.font.Font(None, 36)
            scratch_text = scratch_font.render("SCRATCH HERE!", True, (100, 100, 100))
            scratch_rect = scratch_text.get_rect(center=(self.width//2, self.height//2))
            self.scratch_surface.blit(scratch_text, scratch_rect)

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
            old_percent = self.scratch_percent

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
                "color": self.config["scratch_color"],
                "new_reveal": self.scratch_percent > old_percent
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

    def set_position(self, x, y):
        """Move the ticket to a new position."""
        self.x = x
        self.y = y

    def get_handle_rect(self):
        """Return the grab-handle rectangle at the top of the ticket."""
        return pygame.Rect(self.x, self.y, self.width, self.handle_height)

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

        # Draw drag handle strip at top
        handle_rect = pygame.Rect(self.x, self.y, self.width, self.handle_height)
        handle_surf = pygame.Surface((self.width, self.handle_height), pygame.SRCALPHA)
        handle_surf.fill((0, 0, 0, 60))  # semi-transparent dark overlay
        screen.blit(handle_surf, (self.x, self.y))
        # Grip lines
        for i in range(3):
            ly = self.y + 9 + i * 6
            pygame.draw.line(screen, (180, 180, 180),
                             (self.x + self.width // 2 - 20, ly),
                             (self.x + self.width // 2 + 20, ly), 1)

    def get_rect(self):
        """Get the ticket's bounding rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Match3Ticket:
    """A scratch ticket where you need to match 3 symbols to win."""

    # Default layout — every value can be overridden per-ticket via config["layout"]
    TICKET_WIDTH = 340
    TICKET_HEIGHT = 400
    GRID_PADDING = 20      # padding around the grid (used when auto-centering)
    HEADER_HEIGHT = 45     # space reserved above the grid
    FOOTER_HEIGHT = 30     # space reserved below the grid
    CELL_PADDING = 8       # gap between cells
    CELL_SIZE = None       # None = auto-calculate from available space

    def __init__(self, ticket_type, x, y, width=340, height=280, luck_bonus=0):
        self.ticket_type = ticket_type
        self.config = TICKET_TYPES[ticket_type]
        self.x = x
        self.y = y
        self.luck_bonus = luck_bonus

        # ---- Read per-ticket layout overrides from config ----
        layout = self.config.get("layout", {})

        self.width = layout.get("ticket_width", self.TICKET_WIDTH)
        self.height = layout.get("ticket_height", self.TICKET_HEIGHT)

        self._grid_padding = layout.get("grid_padding", self.GRID_PADDING)
        self._header_height = layout.get("header_height", self.HEADER_HEIGHT)
        self._footer_height = layout.get("footer_height", self.FOOTER_HEIGHT)
        self._cell_padding = layout.get("cell_padding", self.CELL_PADDING)
        self._cell_size_override = layout.get("cell_size", self.CELL_SIZE)

        # Optional: pin the grid's top-left corner to an exact position
        # instead of auto-centering.  None = auto-center (original behaviour).
        self._grid_x = layout.get("grid_x", None)
        self._grid_y = layout.get("grid_y", None)

        # Drag handle
        self.handle_height = 28
        self.dragging = False
        self.drag_offset = (0, 0)

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
        """Calculate the grid layout.  Respects per-ticket overrides from config."""

        # --- Cell size ---
        if self._cell_size_override is not None:
            self.cell_size = self._cell_size_override
        else:
            # Auto-calculate from available space (original behaviour)
            grid_width = self.width - (self._grid_padding * 2)
            grid_height = self.height - self._header_height - self._footer_height - self._grid_padding
            self.cell_size = min(grid_width // 3, grid_height // 3) - self._cell_padding

        # Actual grid pixel dimensions
        actual_grid_width = (self.cell_size * 3) + (self._cell_padding * 2)
        actual_grid_height = (self.cell_size * 3) + (self._cell_padding * 2)

        # --- Grid origin ---
        if self._grid_x is not None:
            self.grid_start_x = self._grid_x
        else:
            self.grid_start_x = (self.width - actual_grid_width) // 2

        if self._grid_y is not None:
            self.grid_start_y = self._grid_y
        else:
            avail = self.height - self._header_height - self._footer_height - self._grid_padding
            self.grid_start_y = self._header_height + (avail - actual_grid_height) // 2

        # --- Build cell positions ---
        self.cell_centers = []
        self.cell_bounds = []

        for i in range(9):
            row = i // 3
            col = i % 3

            cx = self.grid_start_x + col * (self.cell_size + self._cell_padding) + self.cell_size // 2
            cy = self.grid_start_y + row * (self.cell_size + self._cell_padding) + self.cell_size // 2

            self.cell_centers.append((cx, cy))

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
        # Base ticket surface (custom PNG or fallback procedural)
        self.base_surface = pygame.Surface((self.width, self.height))
        has_custom_base = False

        base_img_name = self.config.get("base_image")
        if base_img_name and base_img_name in TICKET_IMAGES:
            scaled = pygame.transform.scale(TICKET_IMAGES[base_img_name],
                                            (self.width, self.height))
            self.base_surface.blit(scaled, (0, 0))
            has_custom_base = True
        else:
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

        # Skip decorative grid/cell backgrounds when using custom base art
        if not has_custom_base:
            grid_bg_rect = pygame.Rect(
                self.grid_start_x - 10,
                self.grid_start_y - 10,
                (self.cell_size * 3) + (self._cell_padding * 2) + 20,
                (self.cell_size * 3) + (self._cell_padding * 2) + 20
            )
            pygame.draw.rect(self.base_surface, (255, 255, 240), grid_bg_rect, border_radius=10)
            pygame.draw.rect(self.base_surface, (200, 180, 100), grid_bg_rect, 3, border_radius=10)

        # Draw the 3x3 grid of symbols (always — this is dynamic game data)
        for i, sym in enumerate(self.symbols):
            cx, cy = self.cell_centers[i]
            is_winner = i in self.winning_positions
            self._draw_symbol(cx, cy, sym, self.cell_size, is_winner, has_custom_base)

        # Draw prize info at bottom if winner
        if self.prize > 0:
            prize_font = pygame.font.Font(None, 28)
            prize_text = prize_font.render(f"WIN ${self.prize}!", True, (50, 180, 50))
            self.base_surface.blit(prize_text,
                (self.width//2 - prize_text.get_width()//2, self.height - 28))

        # Scratch layer (custom PNG or fallback solid color)
        self.scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        scratch_img_name = self.config.get("scratch_image")
        if scratch_img_name and scratch_img_name in TICKET_IMAGES:
            # Use custom pixel-art cover scaled to ticket size
            scaled = pygame.transform.scale(TICKET_IMAGES[scratch_img_name],
                                            (self.width, self.height))
            self.scratch_surface.blit(scaled, (0, 0))
        else:
            # Fallback: solid scratch color with texture
            self.scratch_surface.fill((*self.config["scratch_color"], 255))

            scratch_font = pygame.font.Font(None, 26)
            scratch_text = scratch_font.render("SCRATCH TO REVEAL!", True, (100, 100, 100))
            self.scratch_surface.blit(scratch_text,
                (self.width//2 - scratch_text.get_width()//2, 10))

            for _ in range(30):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                color = tuple(c + random.randint(-10, 10) for c in self.config["scratch_color"])
                color = tuple(max(0, min(255, c)) for c in color)
                pygame.draw.circle(self.scratch_surface, (*color, 255), (x, y), random.randint(1, 4))

        # Draw cell indicator boxes on top (always drawn so player knows where to scratch)
        # Optionally uses custom PNGs for the cell box and/or icon instead of procedural drawing
        cover_img_name = self.config.get("cell_cover_image")
        icon_img_name = self.config.get("cell_icon_image")

        q_font = pygame.font.Font(None, int(self.cell_size * 0.6))
        for i in range(9):
            cx, cy = self.cell_centers[i]

            cell_rect = pygame.Rect(
                cx - self.cell_size // 2 + 2,
                cy - self.cell_size // 2 + 2,
                self.cell_size - 4,
                self.cell_size - 4
            )

            # Cell box: custom PNG or fallback rect
            if cover_img_name and cover_img_name in TICKET_IMAGES:
                cover = pygame.transform.scale(TICKET_IMAGES[cover_img_name],
                                               (cell_rect.width, cell_rect.height))
                self.scratch_surface.blit(cover, cell_rect.topleft)
            else:
                pygame.draw.rect(self.scratch_surface, (150, 130, 150, 255), cell_rect, border_radius=8)
                pygame.draw.rect(self.scratch_surface, (120, 100, 120, 255), cell_rect, 2, border_radius=8)

            # Cell icon: custom PNG or fallback "?" text
            if icon_img_name and icon_img_name in TICKET_IMAGES:
                icon_size = int(min(cell_rect.width, cell_rect.height) * 0.6)
                icon = pygame.transform.scale(TICKET_IMAGES[icon_img_name],
                                              (icon_size, icon_size))
                icon_rect = icon.get_rect(center=cell_rect.center)
                self.scratch_surface.blit(icon, icon_rect)
            else:
                q_text = q_font.render("?", True, (80, 60, 80))
                self.scratch_surface.blit(q_text, (cx - q_text.get_width()//2, cy - q_text.get_height()//2))

    def _draw_symbol(self, cx, cy, symbol_name, cell_size, is_winner=False, has_custom_base=False):
        """Draw a symbol using sprite images instead of procedural shapes."""

        # Skip cell background chrome when using custom base art
        if not has_custom_base:
            if is_winner:
                pygame.draw.rect(self.base_surface, (255, 255, 150),
                                 (cx - cell_size // 2 + 2, cy - cell_size // 2 + 2, cell_size - 4, cell_size - 4),
                                 border_radius=8)

            pygame.draw.rect(self.base_surface, (255, 255, 255),
                             (cx - cell_size // 2 + 4, cy - cell_size // 2 + 4, cell_size - 8, cell_size - 8),
                             border_radius=6)
            pygame.draw.rect(self.base_surface, (200, 200, 200),
                             (cx - cell_size // 2 + 4, cy - cell_size // 2 + 4, cell_size - 8, cell_size - 8),
                             2, border_radius=6)

        # Sprite drawing (always — this is the actual game content)
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
            old_revealed = sum(self.cells_revealed)

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
                "color": self.config["scratch_color"],
                "new_reveal": sum(self.cells_revealed) > old_revealed
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

    def set_position(self, x, y):
        """Move the ticket to a new position."""
        self.x = x
        self.y = y

    def get_handle_rect(self):
        """Return the grab-handle rectangle at the top of the ticket."""
        return pygame.Rect(self.x, self.y, self.width, self.handle_height)

    def draw(self, screen):
        screen.blit(self.base_surface, (self.x, self.y))
        screen.blit(self.scratch_surface, (self.x, self.y))
        pygame.draw.rect(screen, (80, 60, 40),
                        (self.x - 2, self.y - 2, self.width + 4, self.height + 4),
                        4, border_radius=12)

        # Draw drag handle strip at top
        handle_surf = pygame.Surface((self.width, self.handle_height), pygame.SRCALPHA)
        handle_surf.fill((0, 0, 0, 60))
        screen.blit(handle_surf, (self.x, self.y))
        # Grip lines
        for i in range(3):
            ly = self.y + 9 + i * 6
            pygame.draw.line(screen, (180, 180, 180),
                             (self.x + self.width // 2 - 20, ly),
                             (self.x + self.width // 2 + 20, ly), 1)

        # Draw progress indicator (cells revealed)
        revealed = self.get_cells_revealed_count()
        if revealed < 9 and self.scratched:
            font = pygame.font.Font(None, 20)
            progress_text = font.render(f"{revealed}/9 revealed", True, (200, 200, 200))
            screen.blit(progress_text,
                (self.x + self.width//2 - progress_text.get_width()//2, self.y + self.height + 5))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class NumberMatchTicket:
    """A scratch ticket with 5 winning numbers at top, 4x5 grid of your numbers with prizes,
    and a bonus multiplier box. Match any of your numbers to a winning number to win that prize."""

    # Default layout — every value can be overridden per-ticket via config["layout"]
    TICKET_WIDTH = 380
    TICKET_HEIGHT = 420
    HEADER_HEIGHT = 42
    WINNING_ROW_HEIGHT = 50
    GRID_TOP_MARGIN = 8
    CELL_W = 50
    CELL_H = 48
    CELL_PAD = 4
    MULTIPLIER_W = 52
    FOOTER_HEIGHT = 10

    def __init__(self, ticket_type, x, y, width=380, height=420, luck_bonus=0):
        self.ticket_type = ticket_type
        self.config = TICKET_TYPES[ticket_type]
        self.x = x
        self.y = y
        self.luck_bonus = luck_bonus

        # ---- Read per-ticket layout overrides from config ----
        layout = self.config.get("layout", {})

        self.width = layout.get("ticket_width", self.TICKET_WIDTH)
        self.height = layout.get("ticket_height", self.TICKET_HEIGHT)

        self._header_height = layout.get("header_height", self.HEADER_HEIGHT)
        self._win_row_h = layout.get("winning_row_height", self.WINNING_ROW_HEIGHT)
        self._grid_top_margin = layout.get("grid_top_margin", self.GRID_TOP_MARGIN)

        # Grid cell dimensions
        self._cell_w = layout.get("cell_w", self.CELL_W)
        self._cell_h = layout.get("cell_h", self.CELL_H)
        self._cell_pad = layout.get("cell_pad", self.CELL_PAD)

        # Winning row cell dimensions — defaults to grid cell size if not specified
        self._win_cell_w = layout.get("win_cell_w", self._cell_w)
        self._win_cell_h = layout.get("win_cell_h", self._cell_h)
        self._win_cell_pad = layout.get("win_cell_pad", self._cell_pad)

        # Multiplier box dimensions
        self._mult_w = layout.get("multiplier_w", self.MULTIPLIER_W)
        self._mult_h = layout.get("multiplier_h", 60)

        # Optional: pin sections to exact pixel positions instead of auto-centering.
        # None = auto-center (original behaviour).
        self._win_row_x = layout.get("win_row_x", None)    # left edge of winning-numbers row
        self._win_row_y = layout.get("win_row_y", None)     # vertical center of winning row
        self._grid_x = layout.get("grid_x", None)           # left edge of the 5-col grid
        self._grid_y = layout.get("grid_y", None)            # top edge of the 4-row grid
        self._mult_x = layout.get("multiplier_x", None)     # center-x of multiplier box
        self._mult_y = layout.get("multiplier_y", None)      # center-y of multiplier box

        # Drag handle
        self.handle_height = 28
        self.dragging = False
        self.drag_offset = (0, 0)

        # Generate game data
        self.winning_numbers = self._generate_winning_numbers()
        self.grid_numbers = self._generate_grid_numbers()   # 4 rows x 5 cols
        self.grid_prizes = self._generate_grid_prizes()      # prize under each number
        self.multiplier = self._generate_multiplier()

        # Calculate total prize
        self.prize = self._calculate_prize()

        # Cell tracking: 5 winning + 20 grid + 1 multiplier = 26 cells
        self.num_cells = 26
        self.cells_revealed = [False] * self.num_cells
        # Indices: 0-4 = winning numbers, 5-24 = grid (row-major), 25 = multiplier

        # Calculate cell positions
        self._calculate_layout()

        # Create surfaces
        self._create_surfaces()

        # Scratch tracking
        self.scratched = False
        self.scratch_percent = 0
        self.revealed = False

    def _generate_winning_numbers(self):
        """Generate 5 unique winning numbers (1-30)."""
        return random.sample(range(1, 31), 5)

    def _generate_grid_numbers(self):
        """Generate 4x5 grid of numbers. Luck bonus increases match chance."""
        numbers = []
        match_chance = 0.15 + (self.luck_bonus * 0.03)  # 15% base per cell

        for _ in range(20):
            if random.random() < match_chance:
                # Force a match with one of the winning numbers
                numbers.append(random.choice(self.winning_numbers))
            else:
                numbers.append(random.randint(1, 30))
        return numbers

    def _generate_grid_prizes(self):
        """Generate a prize value for each of the 20 grid cells."""
        prize_pool = self.config["cell_prizes"]
        return [random.choice(prize_pool) for _ in range(20)]

    def _generate_multiplier(self):
        """Generate the bonus multiplier (1x, 2x, 3x, 5x)."""
        multiplier_weights = self.config.get("multipliers", [1, 1, 1, 1, 1, 2, 2, 3, 5])
        return random.choice(multiplier_weights)

    def _calculate_prize(self):
        """Calculate total prize: sum of prizes for matched numbers * multiplier."""
        total = 0
        for i, num in enumerate(self.grid_numbers):
            if num in self.winning_numbers:
                total += self.grid_prizes[i]
        return total * self.multiplier

    def _calculate_layout(self):
        """Calculate positions and bounds for all scratchable cells.
        Respects per-ticket overrides from config['layout'].
        Winning row, grid, and multiplier each have independent position + size."""
        self.cell_centers = []
        self.cell_bounds = []

        grid_total_w = 5 * self._cell_w + 4 * self._cell_pad
        win_total_w = 5 * self._win_cell_w + 4 * self._win_cell_pad

        # --- Auto-center X baselines ---
        auto_grid_x = (self.width - grid_total_w - self._mult_w - 8) // 2
        auto_win_x = (self.width - win_total_w) // 2

        # --- Winning numbers row (5 cells, independent size) ---
        win_start_x = self._win_row_x if self._win_row_x is not None else auto_win_x
        win_row_cy = self._win_row_y if self._win_row_y is not None else (self._header_height + self._win_row_h // 2)

        for col in range(5):
            cx = win_start_x + col * (self._win_cell_w + self._win_cell_pad) + self._win_cell_w // 2
            cy = win_row_cy
            self.cell_centers.append((cx, cy))
            self.cell_bounds.append(pygame.Rect(
                cx - self._win_cell_w // 2, cy - self._win_cell_h // 2,
                self._win_cell_w, self._win_cell_h))

        # --- Grid numbers (4 rows x 5 cols) ---
        grid_start_x = self._grid_x if self._grid_x is not None else auto_grid_x
        grid_top = self._grid_y if self._grid_y is not None else (self._header_height + self._win_row_h + self._grid_top_margin)

        for row in range(4):
            for col in range(5):
                cx = grid_start_x + col * (self._cell_w + self._cell_pad) + self._cell_w // 2
                cy = grid_top + row * (self._cell_h + self._cell_pad) + self._cell_h // 2
                self.cell_centers.append((cx, cy))
                self.cell_bounds.append(pygame.Rect(
                    cx - self._cell_w // 2, cy - self._cell_h // 2,
                    self._cell_w, self._cell_h))

        # --- Multiplier box ---
        if self._mult_x is not None:
            mult_cx = self._mult_x
        else:
            mult_cx = grid_start_x + grid_total_w + 8 + self._mult_w // 2

        if self._mult_y is not None:
            mult_cy = self._mult_y
        else:
            mult_cy = grid_top + (4 * (self._cell_h + self._cell_pad)) // 2

        self.cell_centers.append((mult_cx, mult_cy))
        self.cell_bounds.append(pygame.Rect(
            mult_cx - self._mult_w // 2, mult_cy - self._mult_h // 2,
            self._mult_w, self._mult_h))

    def _create_surfaces(self):
        """Create base and scratch surfaces."""
        self.base_surface = pygame.Surface((self.width, self.height))
        has_custom_base = False

        base_img_name = self.config.get("base_image")
        if base_img_name and base_img_name in TICKET_IMAGES:
            scaled = pygame.transform.scale(TICKET_IMAGES[base_img_name],
                                            (self.width, self.height))
            self.base_surface.blit(scaled, (0, 0))
            has_custom_base = True
        else:
            self.base_surface.fill(self.config["color"])

            # Border
            pygame.draw.rect(self.base_surface, (255, 255, 255),
                             (0, 0, self.width, self.height), 4, border_radius=12)

            # Title
            font = pygame.font.Font(None, 30)
            name_text = font.render(self.config["name"], True, (255, 255, 255))
            self.base_surface.blit(name_text,
                (self.width // 2 - name_text.get_width() // 2, 8))

            # Subtitle
            small_font = pygame.font.Font(None, 20)
            sub = small_font.render("Match YOUR numbers to WINNING numbers!", True, (255, 255, 200))
            self.base_surface.blit(sub, (self.width // 2 - sub.get_width() // 2, 28))

        # --- Draw winning numbers section ---
        label_font = pygame.font.Font(None, 16)

        if not has_custom_base:
            win_bg = pygame.Rect(self.cell_bounds[0].x - 6, self._header_height - 2,
                                 self.cell_bounds[4].right - self.cell_bounds[0].x + 12,
                                 self._win_row_h + 4)
            pygame.draw.rect(self.base_surface, (255, 230, 180), win_bg, border_radius=8)
            pygame.draw.rect(self.base_surface, (200, 160, 80), win_bg, 2, border_radius=8)

            win_label = label_font.render("WINNING NUMBERS", True, (140, 100, 40))
            self.base_surface.blit(win_label,
                (win_bg.centerx - win_label.get_width() // 2, win_bg.y + 2))

        # Winning numbers text (always — dynamic game data)
        num_font = pygame.font.Font(None, 32)
        for i in range(5):
            cx, cy = self.cell_centers[i]
            cell_rect = self.cell_bounds[i]

            if not has_custom_base:
                pygame.draw.rect(self.base_surface, (255, 255, 240),
                                 cell_rect, border_radius=6)
                pygame.draw.rect(self.base_surface, (180, 150, 80),
                                 cell_rect, 2, border_radius=6)

            txt = num_font.render(str(self.winning_numbers[i]), True, (60, 40, 20))
            self.base_surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2 + 4))

        # --- Draw grid section ---
        if not has_custom_base:
            grid_bg = pygame.Rect(
                self.cell_bounds[5].x - 6,
                self.cell_bounds[5].y - 6,
                self.cell_bounds[9].right - self.cell_bounds[5].x + 12,
                self.cell_bounds[24].bottom - self.cell_bounds[5].y + 12)
            pygame.draw.rect(self.base_surface, (240, 240, 255), grid_bg, border_radius=8)
            pygame.draw.rect(self.base_surface, (150, 150, 200), grid_bg, 2, border_radius=8)

        # Grid numbers + prizes (always — dynamic game data)
        num_font_sm = pygame.font.Font(None, 26)
        prize_font = pygame.font.Font(None, 18)

        for i in range(20):
            idx = i + 5
            cx, cy = self.cell_centers[idx]
            cell_rect = self.cell_bounds[idx]
            num = self.grid_numbers[i]
            prize_val = self.grid_prizes[i]
            is_match = num in self.winning_numbers

            if not has_custom_base:
                bg_color = (255, 255, 200) if is_match else (255, 255, 255)
                pygame.draw.rect(self.base_surface, bg_color, cell_rect, border_radius=5)
                pygame.draw.rect(self.base_surface, (180, 180, 200), cell_rect, 2, border_radius=5)

                if is_match:
                    pygame.draw.rect(self.base_surface, (50, 180, 50), cell_rect, 2, border_radius=5)

            # Number (top half of cell)
            txt = num_font_sm.render(str(num), True, (40, 40, 80))
            self.base_surface.blit(txt, (cx - txt.get_width() // 2, cy - 16))

            # Prize (bottom half of cell)
            prize_color = (50, 150, 50) if is_match else (120, 120, 140)
            ptxt = prize_font.render(f"${prize_val}", True, prize_color)
            self.base_surface.blit(ptxt, (cx - ptxt.get_width() // 2, cy + 8))

        # --- Draw multiplier box ---
        mult_cx, mult_cy = self.cell_centers[25]
        mult_rect = self.cell_bounds[25]

        if not has_custom_base:
            pygame.draw.rect(self.base_surface, (255, 220, 100), mult_rect, border_radius=8)
            pygame.draw.rect(self.base_surface, (200, 160, 50), mult_rect, 3, border_radius=8)

            mult_label = label_font.render("BONUS", True, (140, 100, 20))
            self.base_surface.blit(mult_label,
                (mult_cx - mult_label.get_width() // 2, mult_rect.y + 4))

        # Multiplier value (always — dynamic game data)
        mult_font = pygame.font.Font(None, 36)
        mult_txt = mult_font.render(f"{self.multiplier}x", True, (180, 80, 20))
        self.base_surface.blit(mult_txt,
            (mult_cx - mult_txt.get_width() // 2, mult_cy + 2))

        # --- Draw prize total at bottom if winner ---
        if self.prize > 0:
            total_font = pygame.font.Font(None, 26)
            total_txt = total_font.render(f"TOTAL WIN: ${self.prize}!", True, (50, 200, 50))
            self.base_surface.blit(total_txt,
                (self.width // 2 - total_txt.get_width() // 2, self.height - 22))

        # ========== SCRATCH SURFACE (custom PNG or fallback solid color) ==========
        self.scratch_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        scratch_img_name = self.config.get("scratch_image")
        if scratch_img_name and scratch_img_name in TICKET_IMAGES:
            # Use custom pixel-art cover scaled to ticket size
            scaled = pygame.transform.scale(TICKET_IMAGES[scratch_img_name],
                                            (self.width, self.height))
            self.scratch_surface.blit(scaled, (0, 0))
        else:
            # Fallback: solid scratch color with texture
            self.scratch_surface.fill((*self.config["scratch_color"], 255))

            scratch_font = pygame.font.Font(None, 24)
            stxt = scratch_font.render("SCRATCH ALL BOXES!", True, (100, 100, 100))
            self.scratch_surface.blit(stxt,
                (self.width // 2 - stxt.get_width() // 2, 10))

            for _ in range(40):
                tx = random.randint(0, self.width)
                ty = random.randint(0, self.height)
                color = tuple(c + random.randint(-10, 10) for c in self.config["scratch_color"])
                color = tuple(max(0, min(255, c)) for c in color)
                pygame.draw.circle(self.scratch_surface, (*color, 255), (tx, ty), random.randint(1, 4))

        # Draw cell indicator boxes on top (always drawn so player knows where to scratch)
        # Optionally uses custom PNGs for the cell box and/or icon instead of procedural drawing
        cover_img_name = self.config.get("cell_cover_image")
        icon_img_name = self.config.get("cell_icon_image")

        q_font = pygame.font.Font(None, 28)
        for i in range(self.num_cells):
            rect = self.cell_bounds[i]

            # Cell box: custom PNG or fallback rect
            if cover_img_name and cover_img_name in TICKET_IMAGES:
                cover = pygame.transform.scale(TICKET_IMAGES[cover_img_name],
                                               (rect.width, rect.height))
                self.scratch_surface.blit(cover, rect.topleft)
            else:
                pygame.draw.rect(self.scratch_surface, (160, 150, 170, 255),
                                 rect, border_radius=6)
                pygame.draw.rect(self.scratch_surface, (130, 120, 140, 255),
                                 rect, 2, border_radius=6)

            # Cell icon: custom PNG or fallback "?" text
            if icon_img_name and icon_img_name in TICKET_IMAGES:
                icon_size = int(min(rect.width, rect.height) * 0.6)
                icon = pygame.transform.scale(TICKET_IMAGES[icon_img_name],
                                              (icon_size, icon_size))
                icon_rect = icon.get_rect(center=rect.center)
                self.scratch_surface.blit(icon, icon_rect)
            else:
                q = q_font.render("?", True, (90, 80, 100))
                self.scratch_surface.blit(q,
                    (rect.centerx - q.get_width() // 2, rect.centery - q.get_height() // 2))

    def scratch(self, mouse_x, mouse_y, radius=20):
        """Scratch at the given position."""
        local_x = mouse_x - self.x
        local_y = mouse_y - self.y

        if 0 <= local_x < self.width and 0 <= local_y < self.height:
            old_revealed = sum(self.cells_revealed)

            pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (local_x, local_y), radius)
            for _ in range(3):
                ox = local_x + random.randint(-radius // 2, radius // 2)
                oy = local_y + random.randint(-radius // 2, radius // 2)
                sr = random.randint(radius // 3, radius // 2)
                pygame.draw.circle(self.scratch_surface, (0, 0, 0, 0), (ox, oy), sr)

            self.scratched = True
            self._update_cells_revealed()

            return {
                "x": mouse_x,
                "y": mouse_y,
                "color": self.config["scratch_color"],
                "new_reveal": sum(self.cells_revealed) > old_revealed
            }
        return None

    def _update_cells_revealed(self):
        """Check which cells have been sufficiently scratched."""
        for i in range(self.num_cells):
            if self.cells_revealed[i]:
                continue

            rect = self.cell_bounds[i]
            cx = rect.centerx
            cy = rect.centery
            half_w = rect.width // 4
            half_h = rect.height // 4

            sample_count = 0
            revealed_count = 0

            for sx in range(-1, 2):
                for sy in range(-1, 2):
                    px = cx + sx * half_w
                    py = cy + sy * half_h
                    if 0 <= px < self.width and 0 <= py < self.height:
                        sample_count += 1
                        pixel = self.scratch_surface.get_at((px, py))
                        if pixel[3] < 128:
                            revealed_count += 1

            if sample_count > 0 and revealed_count >= max(5, sample_count * 0.6):
                self.cells_revealed[i] = True

        if all(self.cells_revealed) and not self.revealed:
            self.revealed = True

    def is_complete(self):
        """Ticket is complete when all cells are revealed."""
        return all(self.cells_revealed)

    def get_cells_revealed_count(self):
        return sum(self.cells_revealed)

    def get_prize(self):
        return self.prize

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_handle_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.handle_height)

    def draw(self, screen):
        screen.blit(self.base_surface, (self.x, self.y))
        screen.blit(self.scratch_surface, (self.x, self.y))
        pygame.draw.rect(screen, (80, 60, 40),
                         (self.x - 2, self.y - 2, self.width + 4, self.height + 4),
                         4, border_radius=12)

        # Drag handle
        handle_surf = pygame.Surface((self.width, self.handle_height), pygame.SRCALPHA)
        handle_surf.fill((0, 0, 0, 60))
        screen.blit(handle_surf, (self.x, self.y))
        for i in range(3):
            ly = self.y + 9 + i * 6
            pygame.draw.line(screen, (180, 180, 180),
                             (self.x + self.width // 2 - 20, ly),
                             (self.x + self.width // 2 + 20, ly), 1)

        # Progress indicator
        revealed = self.get_cells_revealed_count()
        if revealed < self.num_cells and self.scratched:
            font = pygame.font.Font(None, 20)
            ptxt = font.render(f"{revealed}/{self.num_cells} revealed", True, (200, 200, 200))
            screen.blit(ptxt,
                (self.x + self.width // 2 - ptxt.get_width() // 2, self.y + self.height + 5))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


def create_ticket(ticket_type, x, y, width=300, height=200, luck_bonus=0):
    """Factory function to create the right ticket type."""
    config = TICKET_TYPES[ticket_type]
    ticket_class = config.get("ticket_class", "standard")

    if ticket_class == "match3":
        # Match3 tickets use their own fixed size for proper symbol spacing
        return Match3Ticket(ticket_type, x, y, luck_bonus=luck_bonus)
    elif ticket_class == "number_match":
        return NumberMatchTicket(ticket_type, x, y, luck_bonus=luck_bonus)
    else:
        return ScratchTicket(ticket_type, x, y, width, height, luck_bonus)
