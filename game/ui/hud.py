import pygame


class HUD:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, screen, player):
        # Draw money display at top center
        money_text = self.font.render(f"${player.money:.2f}", True, (100, 220, 100))
        screen.blit(money_text, (self.screen_width // 2 - money_text.get_width() // 2, 15))

        # Draw stats below money
        stats_font = pygame.font.Font(None, 20)
        stats_text = stats_font.render(
            f"Tickets: {player.tickets_scratched}  |  Earned: ${player.total_earned:.0f}  |  Best: ${player.biggest_win}",
            True, (180, 180, 180)
        )
        screen.blit(stats_text, (self.screen_width // 2 - stats_text.get_width() // 2, 55))


class AutoCollectTimer:
    """Visual timer for auto-collect countdown."""

    def __init__(self):
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen, x, y, time_remaining, total_time):
        if time_remaining is None or total_time is None:
            return

        # Draw progress bar background
        bar_width = 150
        bar_height = 20
        bar_rect = pygame.Rect(x - bar_width // 2, y, bar_width, bar_height)

        pygame.draw.rect(screen, (60, 60, 60), bar_rect, border_radius=5)

        # Draw progress fill
        progress = max(0, 1 - (time_remaining / total_time))
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(x - bar_width // 2, y, fill_width, bar_height)
            pygame.draw.rect(screen, (100, 200, 100), fill_rect, border_radius=5)

        pygame.draw.rect(screen, (100, 100, 100), bar_rect, 2, border_radius=5)

        # Draw text
        text = self.font.render(f"Auto-collect: {time_remaining:.1f}s", True, (200, 200, 200))
        screen.blit(text, (x - text.get_width() // 2, y + bar_height + 5))


class StatBar:
    def __init__(
        self,
        player,
        x, y, width, height,
        current_and_max,   # ("current_hunger", "max_hunger")
        color=(80, 180, 80),
        back_color=(40, 40, 40),
        border_color=(0, 0, 0),
        radius=12
    ):
        self.player = player

        # Attribute names
        self.current_attr, self.max_attr = current_and_max

        self.rect = pygame.Rect(x, y, width, height)

        self.color = color
        self.back_color = back_color
        self.border_color = border_color
        self.radius = radius
        self.border = 3

    def get_percent(self):
        current = getattr(self.player, self.current_attr)
        max_value = getattr(self.player, self.max_attr)

        if max_value <= 0:
            return 0

        return max(0, current / max_value)

    def draw(self, screen):
        # Background
        pygame.draw.rect(
            screen,
            self.back_color,
            self.rect,
            border_radius=self.radius
        )

        # Filled
        fill_width = int(self.rect.width * self.get_percent())

        if fill_width > 0:
            fill_rect = pygame.Rect(
                self.rect.x,
                self.rect.y,
                fill_width,
                self.rect.height
            )

            pygame.draw.rect(
                screen,
                self.color,
                fill_rect,
                border_radius=self.radius
            )

        # Border
        pygame.draw.rect(
            screen,
            self.border_color,
            self.rect,
            self.border,
            border_radius=self.radius
        )
