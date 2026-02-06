import pygame

from game.ui.button import Button


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
            btn.base_y = y_pos
            btn.set_enabled(is_unlocked)
            self.ticket_buttons[key] = btn
            y_pos += 60
            self.content_height = len(self.ticket_buttons) * 65
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
        clip_rect = pygame.Rect(
            self.x,
            self.scroll_area_top,
            self.width,
            self.scroll_area_height
        )
        screen.set_clip(clip_rect)
        # Draw buttons
        for btn in self.ticket_buttons.values():
            btn.rect.y = btn.base_y - self.scroll_offset
            btn.draw(screen)
        screen.set_clip(None)
        self.draw_scrollbar(screen)

        subtitle_font = pygame.font.Font(None, 24)
        subtitle = subtitle_font.render("Click a ticket to buy it!", True, (200, 255, 200))
        screen.blit(subtitle, (self.x + 20, self.y + 50))


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


class ItemShopPopup(PopupMenu):
    def __init__(self, screen_width, screen_height):
        super().__init__(
            screen_width, screen_height,
            550, 450,
            "Consumables",
            (40, 40, 60), (80, 80, 140)
        )
        self.item_buttons = {}
        self.item_descriptions = {}
        self.scroll_offset = 0

    def setup_buttons(self, consumable_items, player):
        self.item_buttons = {}
        self.item_descriptions = {}

        y_pos = self.y + 70
        for key, config in consumable_items.items():
            cost = player.get_item_cost(key)
            level = player.inventory.items_in_inventory[key]

            if cost is None:
                text = f"{config['name']} - Level not high enough"
            else:
                text = f"{config['name']} (Amount Owned:{player.inventory.items_in_inventory[key]}) - ${cost}"

                btn = Button(
                    self.x + 20, y_pos,
                    self.width - 40, 45,
                    text, color=(153, 79, 0), font_size=20
                )
                btn.base_y = y_pos

                self.item_buttons[key] = btn
                self.item_descriptions[key] = config["description"]
                y_pos += 65
                self.content_height = len(self.item_buttons) * 65
                self.max_scroll = max(0, self.content_height - self.scroll_area_height)

    def update(self, mouse_pos, mouse_clicked, player, items):
        if not self.is_open:
            return None

        super().update(mouse_pos, mouse_clicked)

        bought = None

        for key, btn in self.item_buttons.items():
            cost = player.get_item_cost(key)
            player_level = player.player_level
            item_level = player.inventory.all_game_items[key]['unlock_level']
            can_afford = cost is not None and player.can_afford(cost)
            is_unlocked = player_level >= item_level
            config = items[key]
            if cost is None:
                text = f"{config['name']} - Level not high enough"
            else:
                text = f"{config['name']} (Amount Owned:{player.inventory.items_in_inventory[key]}) - ${cost}"
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
        for key, btn in self.item_buttons.items():
            btn.rect.y = btn.base_y - self.scroll_offset
            btn.draw(screen)

            # Draw description below button
            desc = self.item_descriptions.get(key, "")
            desc_surface = self.desc_font.render(desc, True, (180, 180, 200))
            screen.blit(desc_surface, (btn.rect.x + 10, btn.rect.bottom + 2))

        # Remove clipping
        screen.set_clip(None)

        # Draw scrollbar on top
        self.draw_scrollbar(screen)


class InventoryPopup(PopupMenu):
    """Popup menu for using purchased items."""

    def __init__(self, screen_width, screen_height):
        super().__init__(
            screen_width, screen_height,
            500, 500,
            "INVENTORY",
            (40, 60, 40), (80, 140, 80)
        )
        self.inventory_buttons = {}
        self.inventory_descriptions = {}
        self.scroll_offset = 0

    def setup_buttons(self, player):
        self.inventory_buttons = {}
        self.inventory_descriptions = {}

        y_pos = self.y + 70

        for key, config in player.inventory.all_game_items.items():
            owned = player.inventory.items_in_inventory.get(key, 0)

            # SKIP items player doesn't own
            if owned <= 0:
                continue
            name = config["name"]

            text = f"{name} - Owned: {owned}"

            btn = Button(
                self.x + 20, y_pos,
                self.width - 40, 80,
                text,
                color=(70, 70, 110),
                font_size=22
            )

            btn.base_y = y_pos

            self.inventory_buttons[key] = btn
            self.inventory_descriptions[key] = config["description"]

            y_pos += 80

        self.content_height = len(self.inventory_buttons) * 80
        self.max_scroll = max(0, self.content_height - self.scroll_area_height)

    def update(self, mouse_pos, mouse_clicked, player):
        if not self.is_open:
            return None

        super().update(mouse_pos, mouse_clicked)

        used_item = None

        for key, btn in self.inventory_buttons.items():
            config = player.inventory.all_game_items[key]
            owned = player.inventory.items_in_inventory.get(key, 0)
            name = config["name"]

            # Enable only if player owns at least one
            btn.set_enabled(owned > 0)

            # Update button text
            btn.set_text(f"{name} - Owned: {owned}")

            if btn.update(mouse_pos, mouse_clicked):
                used_item = key

        return used_item

    def draw(self, screen):
        if not self.is_open:
            return

        self.draw_base(screen)

        clip_rect = pygame.Rect(
            self.x,
            self.scroll_area_top,
            self.width,
            self.scroll_area_height
        )
        screen.set_clip(clip_rect)

        for key, btn in self.inventory_buttons.items():
            btn.rect.y = btn.base_y - self.scroll_offset
            btn.draw(screen)

            desc = self.inventory_descriptions.get(key, "")
            desc_surface = self.desc_font.render(desc, True, (180, 180, 200))
            screen.blit(desc_surface, (btn.rect.x + 10, btn.rect.bottom + 2))

        screen.set_clip(None)

        self.draw_scrollbar(screen)


class TicketInventoryPopup(PopupMenu):
    """Popup menu for viewing and selecting purchased tickets."""

    def __init__(self, screen_width, screen_height):
        super().__init__(
            screen_width, screen_height,
            550, 500,
            "MY TICKETS",
            (50, 40, 60), (120, 80, 140)
        )
        self.ticket_buttons = {}
        self.ticket_refs = {}
        self.scroll_offset = 0

    def setup_buttons(self, current_ticket, ticket_queue):
        """Build buttons from current_ticket + ticket_queue."""
        self.ticket_buttons = {}
        self.ticket_refs = {}

        # Build unified list: current ticket first (marked), then queue
        all_tickets = []
        if current_ticket is not None:
            all_tickets.append((current_ticket, True))
        for t in ticket_queue:
            all_tickets.append((t, False))

        y_pos = self.y + 70
        for i, (ticket, is_current) in enumerate(all_tickets):
            label = self._ticket_label(ticket, is_current)
            color = self._ticket_button_color(ticket, is_current)

            btn = Button(
                self.x + 20, y_pos,
                self.width - 40, 60,
                label,
                color=color,
                font_size=20
            )
            btn.base_y = y_pos

            # Current ticket is already active, disable clicking
            if is_current:
                btn.set_enabled(False)

            self.ticket_buttons[i] = btn
            self.ticket_refs[i] = ticket
            y_pos += 70

        self.content_height = len(self.ticket_buttons) * 70
        self.max_scroll = max(0, self.content_height - self.scroll_area_height)

    def _ticket_label(self, ticket, is_current):
        """Build display string for a ticket button."""
        config = ticket.config
        name = config["name"]

        # Determine scratch status
        if ticket.is_complete():
            status = "DONE - Collect!"
        elif hasattr(ticket, 'cells_revealed'):
            # Match3 ticket
            revealed = ticket.get_cells_revealed_count()
            status = f"{revealed}/9 revealed"
        elif ticket.scratched:
            pct = int(ticket.scratch_percent * 100)
            status = f"{pct}% scratched"
        else:
            status = "Unscratched"

        prefix = "[ACTIVE] " if is_current else ""
        return f"{prefix}{name} - {status}"

    def _ticket_button_color(self, ticket, is_current):
        """Get button color based on ticket state."""
        if is_current:
            return (80, 80, 50)
        elif ticket.is_complete():
            return (60, 120, 60)
        elif ticket.scratched:
            return (100, 80, 60)
        else:
            r, g, b = ticket.config["color"]
            return (max(0, r - 40), max(0, g - 40), max(0, b - 40))

    def update(self, mouse_pos, mouse_clicked, current_ticket, ticket_queue):
        """Update popup. Returns clicked ticket object or None."""
        if not self.is_open:
            return None

        super().update(mouse_pos, mouse_clicked)

        clicked_ticket = None
        for i, btn in self.ticket_buttons.items():
            if btn.update(mouse_pos, mouse_clicked):
                clicked_ticket = self.ticket_refs[i]

        return clicked_ticket

    def draw(self, screen):
        if not self.is_open:
            return

        self.draw_base(screen)

        # Subtitle
        subtitle_font = pygame.font.Font(None, 24)
        count = len(self.ticket_refs)
        subtitle = subtitle_font.render(
            f"Click a ticket to switch to it! ({count} ticket{'s' if count != 1 else ''})",
            True, (200, 200, 255)
        )
        screen.blit(subtitle, (self.x + 20, self.y + 50))

        # Clipped scroll area
        clip_rect = pygame.Rect(
            self.x,
            self.scroll_area_top,
            self.width,
            self.scroll_area_height
        )
        screen.set_clip(clip_rect)

        for i, btn in self.ticket_buttons.items():
            btn.rect.y = btn.base_y - self.scroll_offset
            btn.draw(screen)

        screen.set_clip(None)
        self.draw_scrollbar(screen)
