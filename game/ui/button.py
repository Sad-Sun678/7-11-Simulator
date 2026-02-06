import pygame


class Button:
    def __init__(self, x, y, width, height, text, color=(100, 150, 200),
                 hover_color=(130, 180, 230), text_color=(255, 255, 255),
                 disabled_color=(100, 100, 100), font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.font = pygame.font.Font(None, font_size)
        self.enabled = True
        self.hovered = False
        self.clicked = False

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_text(self, text):
        self.text = text

    def set_enabled(self, enabled):
        self.enabled = enabled

    def update(self, mouse_pos, mouse_clicked):
        """Update button state. Returns True if clicked."""
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled

        was_clicked = False
        if self.hovered and mouse_clicked and not self.clicked:
            was_clicked = True

        self.clicked = mouse_clicked and self.hovered
        return was_clicked

    def draw(self, screen):
        # Determine color
        if not self.enabled:
            color = self.disabled_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color

        # Draw button background with rounded corners
        pygame.draw.rect(screen, color, self.rect, border_radius=10)

        # Draw border
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(screen, border_color, self.rect, 3, border_radius=10)

        # Draw text
        text_color = self.text_color if self.enabled else (150, 150, 150)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class Panel:
    def __init__(self, x, y, width, height, color=(60, 60, 80), border_color=(100, 100, 120)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.border_color = border_color

    def draw(self, screen):
        # Draw panel background
        pygame.draw.rect(screen, self.color, self.rect, border_radius=15)
        # Draw border
        pygame.draw.rect(screen, self.border_color, self.rect, 3, border_radius=15)
