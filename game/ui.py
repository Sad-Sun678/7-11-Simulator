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
    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def draw(self, screen, player):
        # Draw money display at top
        money_text = self.font.render(f"${player.money:.2f}", True, (100, 220, 100))
        screen.blit(money_text, (20, 20))

        # Draw stats on right side
        stats = [
            f"Tickets: {player.tickets_scratched}",
            f"Earned: ${player.total_earned:.0f}",
            f"Best Win: ${player.biggest_win}",
        ]

        y = 70
        for stat in stats:
            text = self.small_font.render(stat, True, (200, 200, 200))
            screen.blit(text, (self.screen_width - text.get_width() - 50, y))
            y += 25


class MessagePopup:
    def __init__(self):
        self.messages = []  # List of (text, color, timer)
        self.font = pygame.font.Font(None, 48)

    def add_message(self, text, color=(255, 255, 100), duration=2.0,flag = None):
        self.messages.append({
            "text": text,
            "color": color,
            "timer": duration,
            "alpha": 255,
            "flag":flag
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
                rect = text_surface.get_rect(center=(center_x - 20, center_y + 200 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            elif msg['flag'] == "WIN_PRIZE":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x - 29, center_y + 230 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            elif msg['flag'] == "TRY_AGAIN":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x - 29, center_y - 180 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50

            else:
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x, center_y - 100 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50


class TicketShopUI:
    def __init__(self, x, y, width, height):
        self.panel = Panel(x, y, width, height, (50, 70, 50), (80, 120, 80))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.buttons = []
        self.ticket_buttons = {}
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 36)

    def setup_buttons(self, ticket_types, unlocked_tickets):
        """Create buttons for each ticket type."""
        self.buttons = []
        self.ticket_buttons = {}

        y_pos = self.y + 50
        for key in ticket_types:
            config = ticket_types[key]
            is_unlocked = key in unlocked_tickets

            if is_unlocked:
                text = f"{config['name']} (${config['cost']})"
                color = config["color"]
            else:
                text = f"??? (${config['unlock_threshold']} to unlock)"
                color = (80, 80, 80)

            btn = Button(self.x + 20, y_pos, self.width - 40, 40, text,
                        color=color, font_size=22)
            btn.set_enabled(is_unlocked)
            self.buttons.append(btn)
            self.ticket_buttons[key] = btn
            y_pos += 50

    def update(self, mouse_pos, mouse_clicked, player, ticket_types):
        """Update shop UI. Returns ticket type to buy or None."""
        unlocked = player.get_unlocked_tickets()

        for key, btn in self.ticket_buttons.items():
            is_unlocked = key in unlocked
            config = ticket_types[key]
            can_afford = player.can_afford(config["cost"])

            btn.set_enabled(is_unlocked and can_afford)

            if btn.update(mouse_pos, mouse_clicked):
                return key
        return None

    def draw(self, screen):
        self.panel.draw(screen)

        # Draw title
        title = self.title_font.render("TICKET SHOP", True, (200, 255, 200))
        screen.blit(title, (self.x + self.width // 2 - title.get_width() // 2, self.y + 10))

        # Draw buttons
        for btn in self.buttons:
            btn.draw(screen)


class UpgradeShopUI:
    def __init__(self, x, y, width, height):
        self.panel = Panel(x, y, width, height, (50, 50, 70), (80, 80, 120))
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.buttons = []
        self.upgrade_buttons = {}
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

    def setup_buttons(self, upgrades, player):
        """Create buttons for each upgrade."""
        self.buttons = []
        self.upgrade_buttons = {}

        y_pos = self.y + 50
        for key, config in upgrades.items():
            level = player.upgrades[key]
            cost = player.get_upgrade_cost(key)

            if cost is None:
                text = f"{config['icon']} {config['name']} (MAX)"
            else:
                text = f"{config['icon']} {config['name']} Lv{level} (${cost})"

            btn = Button(self.x + 10, y_pos, self.width - 20, 35, text,
                        color=(80, 80, 120), font_size=20)
            self.buttons.append(btn)
            self.upgrade_buttons[key] = btn
            y_pos += 45

    def update(self, mouse_pos, mouse_clicked, player, upgrades):
        """Update upgrade shop. Returns upgrade key bought or None."""
        for key, btn in self.upgrade_buttons.items():
            cost = player.get_upgrade_cost(key)
            can_afford = cost is not None and player.can_afford(cost)
            btn.set_enabled(can_afford)

            # Update button text
            level = player.upgrades[key]
            config = upgrades[key]
            if cost is None:
                btn.set_text(f"{config['icon']} {config['name']} (MAX)")
            else:
                btn.set_text(f"{config['icon']} {config['name']} Lv{level} (${cost})")

            if btn.update(mouse_pos, mouse_clicked):
                return key
        return None

    def draw(self, screen):
        self.panel.draw(screen)

        # Draw title
        title = self.title_font.render("UPGRADES", True, (200, 200, 255))
        screen.blit(title, (self.x + self.width // 2 - title.get_width() // 2, self.y + 10))

        # Draw buttons
        for btn in self.buttons:
            btn.draw(screen)
