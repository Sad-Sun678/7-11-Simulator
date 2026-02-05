import pygame

class HealthBar:
    def __init__(self, x, y, width, height, text,
                 color=(0, 0, 153), hover_color=(0, 0, 255),
                 font_size=24, text_color=(255, 255, 255)):

        # Static frame
        self.frame_rect = pygame.Rect(x, y, width, height)

        # Dynamic fill
        self.fill_rect = pygame.Rect(x, y, width, height)

        self.max_height = height

        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False
        self.text_color = text_color
        self.enabled = True

    def set_pos(self, x, y):
        self.frame_rect.topleft = (x, y)
        self.fill_rect.bottomleft = self.frame_rect.bottomleft

    # value = current morale / health (pixels)
    def update(self, value):

        # Clamp
        value = max(0, min(self.max_height, value))

        # Change inner height
        self.fill_rect.height = value

        # Keep fill anchored to bottom
        self.fill_rect.bottom = self.frame_rect.bottom

    def draw(self, screen):

        color = self.hover_color if self.hovered else self.color

        # Draw inside (shrinking bar)
        pygame.draw.rect(screen, color, self.fill_rect, border_radius=50)

        # Draw border (never changes)
        border_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.rect(screen, border_color, self.frame_rect, 3, border_radius=10)

        # Draw text centered on frame
        text_color = self.text_color if self.enabled else (150, 150, 150)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.frame_rect.center)
        screen.blit(text_surface, text_rect)



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


class MessagePopup:
    def __init__(self):
        self.messages = []
        self.font = pygame.font.Font(None, 48)

    def add_message(self, text, color=(255, 255, 100), duration=2.0, flag=None):
        self.messages.append({
            "text": text,
            "color": color,
            "timer": duration,
            "alpha": 255,
            "flag": flag
        })

    def update(self, dt):
        for msg in self.messages[:]:
            msg["timer"] -= dt
            if msg["timer"] < 0.5:
                msg["alpha"] = int(255 * (msg["timer"] / 0.5))
            if msg["timer"] <= 0:
                self.messages.remove(msg)

    def draw(self, screen, center_x, center_y):
        y_offset = 0
        for msg in self.messages:
            if msg['flag'] == "AMOUNT_TEXT":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x, center_y + 120 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            elif msg['flag'] == "WIN_PRIZE":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x, center_y + 150 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            elif msg['flag'] == "TRY_AGAIN":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x, center_y - 120 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            else:
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x, center_y - 100 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50


class PopupMenu:
    """Base class for scrollable popup menus."""

    # Layout constants
    HEADER_HEIGHT = 70  # Space for title and subtitle
    FOOTER_HEIGHT = 20  # Bottom padding
    SCROLL_SPEED = 30   # Pixels per scroll tick

    def __init__(self, screen_width, screen_height, width, height, title, bg_color, border_color):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = width
        self.height = height
        self.title = title
        self.bg_color = bg_color
        self.border_color = border_color

        # Center the popup
        self.x = (screen_width - width) // 2
        self.y = (screen_height - height) // 2

        self.is_open = False
        self.buttons = []

        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.content_height = 0

        # Scrollable area bounds
        self.scroll_area_top = self.y + self.HEADER_HEIGHT
        self.scroll_area_bottom = self.y + self.height - self.FOOTER_HEIGHT
        self.scroll_area_height = self.scroll_area_bottom - self.scroll_area_top

        # Close button
        self.close_button = Button(
            self.x + width - 40, self.y + 10,
            30, 30, "X",
            color=(180, 80, 80), hover_color=(220, 100, 100), font_size=20
        )

        # Fonts
        self.title_font = pygame.font.Font(None, 42)
        self.desc_font = pygame.font.Font(None, 20)

    def open(self):
        self.is_open = True
        self.scroll_offset = 0  # Reset scroll when opening

    def close(self):
        self.is_open = False

    def toggle(self):
        self.is_open = not self.is_open

    def contains_point(self, pos):
        """Check if a point is within the popup."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def is_in_scroll_area(self, pos):
        """Check if a point is within the scrollable area."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.scroll_area_top <= pos[1] <= self.scroll_area_bottom)

    def handle_scroll(self, scroll_y):
        """Handle mouse scroll input. scroll_y is positive for up, negative for down."""
        if not self.is_open:
            return
        self.scroll_offset -= scroll_y * self.SCROLL_SPEED
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def update(self, mouse_pos, mouse_clicked):
        """Base update - handles close button. Returns True if popup consumed the click."""
        if not self.is_open:
            return False

        if self.close_button.update(mouse_pos, mouse_clicked):
            self.close()
            return True

        return self.contains_point(mouse_pos)

    def draw_base(self, screen):
        """Draw the base popup (background, border, title, close button)."""
        if not self.is_open:
            return

        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Draw popup background
        popup_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, self.bg_color, popup_rect, border_radius=20)
        pygame.draw.rect(screen, self.border_color, popup_rect, 4, border_radius=20)

        # Draw title
        title_surface = self.title_font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surface, (self.x + 20, self.y + 15))

        # Draw close button
        self.close_button.draw(screen)

    def draw_scrollbar(self, screen):
        """Draw a scrollbar if content is scrollable."""
        if self.max_scroll <= 0:
            return


        scrollbar_x = self.x + self.width - 15
        scrollbar_track_height = self.scroll_area_height - 20
        scrollbar_y = self.scroll_area_top + 10

        # Draw track
        track_rect = pygame.Rect(scrollbar_x, scrollbar_y, 8, scrollbar_track_height)
        pygame.draw.rect(screen, (50, 50, 60), track_rect, border_radius=4)

        # Calculate thumb size and position
        visible_ratio = self.scroll_area_height / (self.content_height + 1)
        thumb_height = max(30, int(scrollbar_track_height * visible_ratio))
        scroll_ratio = self.scroll_offset / (self.max_scroll + 1)
        thumb_y = scrollbar_y + int((scrollbar_track_height - thumb_height) * scroll_ratio)

        # Draw thumb
        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, 8, thumb_height)
        pygame.draw.rect(screen, (100, 100, 120), thumb_rect, border_radius=4)


class TicketShopPopup(PopupMenu):
    """Popup menu for buying tickets."""

    def __init__(self, screen_width, screen_height):
        super().__init__(
            screen_width, screen_height,
            500, 500,
            "TICKET SHOP",
            (40, 60, 40), (80, 140, 80)
        )
        self.ticket_buttons = {}
        self.scroll_offset = 0


    def setup_buttons(self, ticket_types, unlocked_tickets):
        """Create buttons for each ticket type."""
        self.ticket_buttons = {}

        y_pos = self.y + 70
        for key in ticket_types:
            config = ticket_types[key]
            is_unlocked = key in unlocked_tickets

            if is_unlocked:
                text = f"{config['name']} - ${config['cost']}"
                color = config["color"]
            else:
                text = f"??? - Earn ${config['unlock_threshold']} to unlock"
                color = (80, 80, 80)

            btn = Button(
                self.x + 20, y_pos,
                self.width - 40, 50,
                text, color=color, font_size=24
            )
            btn.set_enabled(is_unlocked)
            self.ticket_buttons[key] = btn
            y_pos += 60
            self.content_height = len(self.ticket_buttons) * 60  # buttons are 60 pixels tall
            self.max_scroll = max(0, self.content_height - self.scroll_area_height)

    def update(self, mouse_pos, mouse_clicked, player, ticket_types):
        """Update shop UI. Returns ticket type to buy or None."""
        if not self.is_open:
            return None

        # Handle base popup (close button, etc.)
        base_consumed = super().update(mouse_pos, mouse_clicked)

        unlocked = player.get_unlocked_tickets()
        bought = None

        for key, btn in self.ticket_buttons.items():
            is_unlocked = key in unlocked
            config = ticket_types[key]
            can_afford = player.can_afford(config["cost"])

            btn.set_enabled(is_unlocked and can_afford)

            # Update button text to show locked status
            if is_unlocked:
                btn.text = f"{config['name']} - ${config['cost']}"
                btn.color = config["color"]
            else:
                btn.text = f"??? - Earn ${config['unlock_threshold']} to unlock"
                btn.color = (80, 80, 80)

            if btn.update(mouse_pos, mouse_clicked):
                bought = key

        return bought

    def draw(self, screen):
        if not self.is_open:
            return

        self.draw_base(screen)

        # Draw subtitle
        subtitle_font = pygame.font.Font(None, 24)
        subtitle = subtitle_font.render("Click a ticket to buy it!", True, (200, 255, 200))
        screen.blit(subtitle, (self.x + 20, self.y + 50))

        # Draw buttons
        for btn in self.ticket_buttons.values():
            btn.draw(screen)


class UpgradeShopPopup(PopupMenu):
    """Popup menu for buying upgrades."""

    def __init__(self, screen_width, screen_height):
        super().__init__(
            screen_width, screen_height,
            550, 450,
            "UPGRADES",
            (40, 40, 60), (80, 80, 140)
        )
        self.upgrade_buttons = {}

        self.upgrade_descriptions = {}


    def setup_buttons(self, upgrades, player):
        """Create buttons for each upgrade."""
        self.upgrade_buttons = {}
        self.upgrade_descriptions = {}

        y_pos = self.y + 70
        for key, config in upgrades.items():
            level = player.upgrades[key]
            cost = player.get_upgrade_cost(key)

            if cost is None:
                text = f"{config['name']} - MAX LEVEL"
            else:
                text = f"{config['name']} (Lv {level}) - ${cost}"

            btn = Button(
                self.x + 20, y_pos,
                self.width - 40, 45,
                text, color=(70, 70, 110), font_size=22
            )
            btn.base_y = y_pos

            self.upgrade_buttons[key] = btn
            self.upgrade_descriptions[key] = config["description"]
            y_pos += 65
            self.content_height = len(self.upgrade_buttons) * 65
            self.max_scroll = max(0, self.content_height - self.scroll_area_height)

    def update(self, mouse_pos, mouse_clicked, player, upgrades):
        """Update upgrade shop. Returns upgrade key bought or None."""
        if not self.is_open:
            return None

        super().update(mouse_pos, mouse_clicked)

        bought = None

        for key, btn in self.upgrade_buttons.items():
            cost = player.get_upgrade_cost(key)
            can_afford = cost is not None and player.can_afford(cost)
            btn.set_enabled(can_afford)

            # Update button text
            level = player.upgrades[key]
            config = upgrades[key]
            if cost is None:
                btn.set_text(f"{config['name']} - MAX LEVEL")
            else:
                btn.set_text(f"{config['name']} (Lv {level}) - ${cost}")

            if btn.update(mouse_pos, mouse_clicked):
                bought = key

        return bought

    def draw(self, screen):
        if not self.is_open:
            return

        self.draw_base(screen)

        # Clip drawing to scroll area
        clip_rect = pygame.Rect(
            self.x,
            self.scroll_area_top,
            self.width,
            self.scroll_area_height
        )
        screen.set_clip(clip_rect)

        # Draw buttons with scrolling
        for key, btn in self.upgrade_buttons.items():
            btn.rect.y = btn.base_y - self.scroll_offset
            btn.draw(screen)

            # Draw description below button
            desc = self.upgrade_descriptions.get(key, "")
            desc_surface = self.desc_font.render(desc, True, (180, 180, 200))
            screen.blit(desc_surface, (btn.rect.x + 10, btn.rect.bottom + 2))

        # Remove clipping
        screen.set_clip(None)

        # Draw scrollbar on top
        self.draw_scrollbar(screen)


class MainMenuButtons:
    """The main screen buttons to open shops."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Button dimensions
        btn_width = 160
        btn_height = 50
        padding = 20

        # Position buttons at bottom of screen
        btn_y = screen_height - btn_height - padding

        # Ticket Shop button (left side)
        self.ticket_shop_btn = Button(
            padding, btn_y,
            btn_width, btn_height,
            "TICKETS",
            color=(60, 120, 60), hover_color=(80, 160, 80), font_size=28
        )

        # Upgrades button (right of ticket shop)
        self.upgrades_btn = Button(
            padding + btn_width + 10, btn_y,
            btn_width, btn_height,
            "UPGRADES",
            color=(60, 60, 120), hover_color=(80, 80, 160), font_size=28
        )

        # Collect button (center, but will be positioned dynamically)
        self.collect_btn = Button(
            screen_width // 2 + 10, btn_y,
            150, btn_height,
            "COLLECT",
            color=(120, 160, 60), hover_color=(160, 200, 80), font_size=28
        )
        self.collect_btn.set_enabled(False)

    def update(self, mouse_pos, mouse_clicked):
        """Update buttons. Returns dict of which buttons were clicked."""
        result = {
            "ticket_shop": self.ticket_shop_btn.update(mouse_pos, mouse_clicked),
            "upgrades": self.upgrades_btn.update(mouse_pos, mouse_clicked),
            "collect": self.collect_btn.update(mouse_pos, mouse_clicked),
        }
        return result

    def set_collect_enabled(self, enabled):
        self.collect_btn.set_enabled(enabled)

    def draw(self, screen):
        self.ticket_shop_btn.draw(screen)
        self.upgrades_btn.draw(screen)

        # Only draw collect if enabled
        if self.collect_btn.enabled:
            self.collect_btn.draw(screen)


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
