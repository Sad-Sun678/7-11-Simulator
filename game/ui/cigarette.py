import pygame


class Cigarette:
    def __init__(
        self,
        idle_image,
        smoking_image,
        x, y, particle_system,
        scale=1.0,
        message="HOLD SPACE TO SMOKE",
        panel_alpha=140
    ):
        self.x = x
        self.y = y
        self.is_smoking = False
        self.particle_system = particle_system

        self.padding = 10
        self.border_thickness = 2
        self.border_color = (220, 40, 40)

        self.panel_alpha = panel_alpha

        self.message = message

        self.font = pygame.font.Font(None, 22)
        self.live_font = pygame.font.Font(None, 20)

        self.text_color = (220, 40, 40)

        # Blink setup
        self.blink_interval = 500  # ms
        self.last_blink = pygame.time.get_ticks()
        self.show_dot = True

        # Scale images ONCE
        idle_w = int(idle_image.get_width() * scale)
        idle_h = int(idle_image.get_height() * scale)

        smoke_w = int(smoking_image.get_width() * scale)
        smoke_h = int(smoking_image.get_height() * scale)

        self.idle_image = pygame.transform.smoothscale(idle_image, (idle_w, idle_h))
        self.smoking_image = pygame.transform.smoothscale(smoking_image, (smoke_w, smoke_h))

        self.image_rect = self.idle_image.get_rect(topleft=(x, y))

        # Frame rect
        self.frame_rect = pygame.Rect(
            self.image_rect.x - self.padding,
            self.image_rect.y - self.padding,
            self.image_rect.width + self.padding * 2,
            self.image_rect.height + self.padding * 2
        )

        # Inner panel surface
        self.panel_surface = pygame.Surface(
            (self.frame_rect.width, self.frame_rect.height),
            pygame.SRCALPHA
        )

        self.panel_surface.fill((0, 0, 0, self.panel_alpha))

    def start_smoking(self):
        self.is_smoking = True

    def stop_smoking(self):
        self.is_smoking = False

    def update_blink(self):
        now = pygame.time.get_ticks()

        if now - self.last_blink > self.blink_interval:
            self.show_dot = not self.show_dot
            self.last_blink = now

    def draw(self, screen, remaining=None, total=None):
        self.update_blink()

        image = self.smoking_image if self.is_smoking else self.idle_image

        # ----- LIVE HEADER -----

        header_y = self.frame_rect.y - 22
        header_x = self.frame_rect.x

        live_text = self.live_font.render("LIVE CIGGY CAM", True, self.text_color)
        screen.blit(live_text, (header_x + 18, header_y))

        # Blinking red dot
        if self.show_dot:
            pygame.draw.circle(
                screen,
                (220, 40, 40),
                (header_x + 8, header_y + 8),
                5
            )

        # ----- PANEL -----

        screen.blit(self.panel_surface, self.frame_rect.topleft)

        pygame.draw.rect(
            screen,
            self.border_color,
            self.frame_rect,
            self.border_thickness
        )

        screen.blit(image, self.image_rect.topleft)

        # Message below
        text_surface = self.font.render(self.message, True, self.text_color)
        text_rect = text_surface.get_rect(
            midtop=(self.frame_rect.centerx, self.frame_rect.bottom + 6)
        )
        if self.is_smoking:
            self.particle_system.add_smoke(
                self.image_rect.right - 50,
                self.image_rect.top + 65
            )
        if not self.is_smoking:
            self.particle_system.add_smoke(
                self.image_rect.right - 200,
                self.image_rect.top+ 200
            )

        screen.blit(text_surface, text_rect)

        # ----- TIMER BAR -----
        if remaining is not None and total is not None and total > 0:
            bar_width = self.frame_rect.width
            bar_height = 6
            bar_x = self.frame_rect.x
            bar_y = text_rect.bottom + 4

            # Background
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=3)

            # Fill (green → red as it depletes)
            pct = max(0, remaining / total)
            fill_w = int(bar_width * pct)
            if fill_w > 0:
                r = int(255 * (1 - pct))
                g = int(200 * pct)
                fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_height)
                pygame.draw.rect(screen, (r, g, 0), fill_rect, border_radius=3)

            pygame.draw.rect(screen, (80, 80, 80), bg_rect, 1, border_radius=3)
