import pygame


class PeeCam:
    """Animated 'LIVE PEE CAM' display using a horizontal spritesheet.
    Shows when the player holds their bladder too long — plays once then signals done.
    """

    def __init__(self, spritesheet_path, x, y, frame_size=128, scale=2.0,
                 animation_speed=0.1, panel_alpha=140):
        self.x = x
        self.y = y
        self.frame_size = frame_size
        self.animation_speed = animation_speed  # seconds per frame

        # Load and slice spritesheet
        sheet = pygame.image.load(spritesheet_path).convert_alpha()
        sheet_width = sheet.get_width()
        num_frames = sheet_width // frame_size

        self.frames = []
        scaled_size = int(frame_size * scale)
        for i in range(num_frames):
            frame_surf = sheet.subsurface(pygame.Rect(
                i * frame_size, 0, frame_size, frame_size
            ))
            frame_surf = pygame.transform.smoothscale(
                frame_surf, (scaled_size, scaled_size)
            )
            self.frames.append(frame_surf)

        self.num_frames = len(self.frames)
        self.scaled_size = scaled_size

        # Animation state
        self.current_frame = 0
        self.frame_timer = 0.0
        self.playing = False
        self.finished = False  # True after animation has played through once

        # Visual layout (mirrors Cigarette style)
        self.padding = 10
        self.border_thickness = 2
        self.border_color = (220, 40, 40)
        self.text_color = (220, 40, 40)
        self.panel_alpha = panel_alpha

        self.font = pygame.font.Font(None, 22)
        self.live_font = pygame.font.Font(None, 20)

        # Image rect
        self.image_rect = pygame.Rect(x, y, scaled_size, scaled_size)

        # Frame rect (panel behind image)
        self.frame_rect = pygame.Rect(
            self.image_rect.x - self.padding,
            self.image_rect.y - self.padding,
            self.image_rect.width + self.padding * 2,
            self.image_rect.height + self.padding * 2
        )

        # Dark panel surface
        self.panel_surface = pygame.Surface(
            (self.frame_rect.width, self.frame_rect.height),
            pygame.SRCALPHA
        )
        self.panel_surface.fill((0, 0, 0, self.panel_alpha))

        # Blink setup for REC dot
        self.blink_interval = 500  # ms
        self.last_blink = pygame.time.get_ticks()
        self.show_dot = True

    def start(self):
        """Start playing the animation from the beginning."""
        self.current_frame = 0
        self.frame_timer = 0.0
        self.playing = True
        self.finished = False

    def stop(self):
        """Stop and reset the animation."""
        self.playing = False
        self.finished = False
        self.current_frame = 0
        self.frame_timer = 0.0

    def update(self, dt):
        """Advance the animation. Returns True when the animation finishes playing."""
        if not self.playing or self.finished:
            return False

        self.frame_timer += dt
        if self.frame_timer >= self.animation_speed:
            self.frame_timer -= self.animation_speed
            self.current_frame += 1

            if self.current_frame >= self.num_frames:
                # Animation played through once — signal done
                self.current_frame = self.num_frames - 1  # hold last frame
                self.finished = True
                self.playing = False
                return True

        return False

    def _update_blink(self):
        now = pygame.time.get_ticks()
        if now - self.last_blink > self.blink_interval:
            self.show_dot = not self.show_dot
            self.last_blink = now

    def draw(self, screen):
        """Draw the pee cam panel with animation, red border, and LIVE header."""
        if not self.playing and not self.finished:
            return

        self._update_blink()

        # ----- LIVE HEADER -----
        header_y = self.frame_rect.y - 22
        header_x = self.frame_rect.x

        live_text = self.live_font.render("LIVE PEE CAM", True, self.text_color)
        screen.blit(live_text, (header_x + 18, header_y))

        # Blinking red REC dot
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

        # Current animation frame
        screen.blit(self.frames[self.current_frame], self.image_rect.topleft)

        # Message below
        msg = "OH NO..."
        text_surface = self.font.render(msg, True, self.text_color)
        text_rect = text_surface.get_rect(
            midtop=(self.frame_rect.centerx, self.frame_rect.bottom + 6)
        )
        screen.blit(text_surface, text_rect)
