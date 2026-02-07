import pygame
from game.ui.button import Button


# ---------------------------------------------------------------------------
# SideMenuTrigger — a small button in the vertical sidebar
# ---------------------------------------------------------------------------
class SideMenuTrigger:
    """A single trigger button in the vertical sidebar."""

    def __init__(self, x, y, width, height, label, icon_text,
                 color, hover_color, font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.icon_text = icon_text
        self.color = color
        self.hover_color = hover_color
        self.active = False
        self.hovered = False
        self.clicked = False  # edge-detection guard

        self.font = pygame.font.Font(None, font_size)
        self.icon_font = pygame.font.Font(None, 28)

    def update(self, mouse_pos, mouse_clicked):
        """Returns True on a single-frame click."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        was_clicked = False
        if self.hovered and mouse_clicked and not self.clicked:
            was_clicked = True
        self.clicked = mouse_clicked and self.hovered
        return was_clicked

    def draw(self, screen):
        if self.active:
            color = self.hover_color
        elif self.hovered:
            # Blend toward hover
            color = tuple(min(255, c + 30) for c in self.color)
        else:
            color = self.color

        # Draw background
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        # Border
        border_color = tuple(max(0, c - 30) for c in color)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=6)

        # Active indicator bar on left edge
        if self.active:
            bar = pygame.Rect(self.rect.x, self.rect.y + 4,
                              3, self.rect.height - 8)
            pygame.draw.rect(screen, (255, 255, 255), bar)

        # Icon character centred
        icon_surf = self.icon_font.render(self.icon_text, True, (255, 255, 255))
        icon_rect = icon_surf.get_rect(center=(self.rect.centerx,
                                                self.rect.centery - 8))
        screen.blit(icon_surf, icon_rect)

        # Tiny label below icon
        label_surf = self.font.render(self.label, True, (220, 220, 220))
        label_rect = label_surf.get_rect(center=(self.rect.centerx,
                                                  self.rect.centery + 14))
        screen.blit(label_surf, label_rect)


# ---------------------------------------------------------------------------
# SideMenuPanel — the glass-like sliding panel
# ---------------------------------------------------------------------------
class SideMenuPanel:
    """A slide-out panel that hosts menu content."""

    SLIDE_SPEED = 1800          # pixels per second
    HEADER_HEIGHT = 55          # title area at top of panel
    SCROLL_SPEED = 30           # pixels per scroll tick
    BTN_SPACING = 60            # vertical distance between button tops
    BTN_HEIGHT = 45
    BTN_PADDING_X = 12
    SCROLL_TOP_PAD = 10

    def __init__(self, panel_width, screen_height, anchor_x, *,
                 alpha=180, bg_color=(40, 45, 55), bg_image_path=None,
                 title="Menu"):
        self.panel_width = panel_width
        self.panel_height = screen_height
        self.anchor_x = anchor_x          # right edge target when open
        self.alpha = alpha
        self.bg_color = bg_color
        self.title = title

        # Slide animation
        self.open_x = anchor_x - panel_width   # left edge when fully open
        self.closed_x = anchor_x               # left edge when fully closed (hidden right)
        self.current_x = float(self.closed_x)  # start hidden
        self.is_open = False
        self.is_animating = False

        # Background image (optional)
        self.bg_image = None
        if bg_image_path:
            try:
                img = pygame.image.load(bg_image_path).convert_alpha()
                self.bg_image = pygame.transform.smoothscale(
                    img, (panel_width, screen_height))
            except Exception:
                self.bg_image = None

        # Panel surface (reused each frame)
        self.surface = pygame.Surface(
            (panel_width, screen_height), pygame.SRCALPHA)

        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.content_height = 0

        # Content — populated externally by the manager's setup_* methods
        self.buttons = []       # list of Button objects
        self.desc_texts = {}    # index -> description string (optional)

        # Fonts
        self.title_font = pygame.font.Font(None, 32)
        self.desc_font = pygame.font.Font(None, 18)

        # Close button (drawn inside the panel)
        self.close_btn = Button(
            panel_width - 36, 10, 28, 28, "X",
            color=(140, 50, 50), hover_color=(200, 60, 60), font_size=20)

    # ---- animation ----

    def animate(self, dt):
        """Slide toward target position."""
        target = self.open_x if self.is_open else self.closed_x

        if self.current_x != target:
            direction = -1 if self.current_x > target else 1
            self.current_x += direction * self.SLIDE_SPEED * dt
            # Clamp
            if direction == -1:
                self.current_x = max(self.current_x, target)
            else:
                self.current_x = min(self.current_x, target)
            self.is_animating = (self.current_x != target)
        else:
            self.is_animating = False

    # ---- hit testing ----

    def get_panel_rect(self):
        """Current on-screen rect of the panel."""
        return pygame.Rect(int(self.current_x), 0,
                           self.panel_width, self.panel_height)

    def contains_point(self, pos):
        return self.get_panel_rect().collidepoint(pos)

    # ---- scrolling ----

    def handle_scroll(self, scroll_y):
        self.scroll_offset -= scroll_y * self.SCROLL_SPEED
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def _recalc_scroll(self):
        scroll_area = self.panel_height - self.HEADER_HEIGHT - 20
        self.max_scroll = max(0, self.content_height - scroll_area)

    # ---- drawing ----

    def draw(self, screen):
        # Don't draw if fully hidden (or very close)
        if self.current_x >= self.closed_x - 1 and not self.is_open:
            return

        panel_x = int(self.current_x)
        panel_rect = pygame.Rect(panel_x, 0,
                                 self.panel_width, self.panel_height)

        # --- glass background ---
        self.surface.fill((0, 0, 0, 0))  # clear
        if self.bg_image:
            self.surface.blit(self.bg_image, (0, 0))
            # apply uniform alpha by subtracting from alpha channel
            alpha_overlay = pygame.Surface(
                (self.panel_width, self.panel_height), pygame.SRCALPHA)
            alpha_overlay.fill((0, 0, 0, 255 - self.alpha))
            self.surface.blit(alpha_overlay, (0, 0),
                              special_flags=pygame.BLEND_RGBA_SUB)
        else:
            self.surface.fill((*self.bg_color, self.alpha))

        screen.blit(self.surface, (panel_x, 0))

        # --- border ---
        border_color = tuple(min(255, c + 40) for c in self.bg_color)
        pygame.draw.rect(screen, border_color, panel_rect, 2, border_radius=4)

        # --- title ---
        title_surf = self.title_font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surf, (panel_x + 14, 14))

        # --- close button ---
        self.close_btn.rect.x = panel_x + self.panel_width - 36
        self.close_btn.draw(screen)

        # --- scrollable content area ---
        scroll_top = self.HEADER_HEIGHT
        scroll_bottom = self.panel_height - 10
        clip = pygame.Rect(panel_x, scroll_top,
                           self.panel_width, scroll_bottom - scroll_top)
        screen.set_clip(clip)

        for idx, btn in enumerate(self.buttons):
            # Position button in screen space
            btn.rect.x = panel_x + self.BTN_PADDING_X
            btn.rect.y = (scroll_top + self.SCROLL_TOP_PAD
                          + idx * self.BTN_SPACING
                          - self.scroll_offset)
            btn.draw(screen)

            # Description text below button
            desc = self.desc_texts.get(idx, "")
            if desc:
                desc_surf = self.desc_font.render(desc, True, (190, 190, 210))
                screen.blit(desc_surf,
                            (btn.rect.x + 8, btn.rect.bottom + 2))

        screen.set_clip(None)

        # --- scrollbar ---
        self._draw_scrollbar(screen, panel_x, scroll_top,
                             scroll_bottom - scroll_top)

    def _draw_scrollbar(self, screen, panel_x, track_y, track_height):
        if self.max_scroll <= 0:
            return
        bar_x = panel_x + self.panel_width - 8
        visible_ratio = track_height / (track_height + self.max_scroll)
        thumb_h = max(20, int(track_height * visible_ratio))
        scroll_ratio = self.scroll_offset / self.max_scroll if self.max_scroll else 0
        thumb_y = track_y + int((track_height - thumb_h) * scroll_ratio)

        # Track
        pygame.draw.rect(screen, (60, 60, 60),
                         pygame.Rect(bar_x, track_y, 6, track_height),
                         border_radius=3)
        # Thumb
        pygame.draw.rect(screen, (140, 140, 160),
                         pygame.Rect(bar_x, thumb_y, 6, thumb_h),
                         border_radius=3)


# ---------------------------------------------------------------------------
# SideMenuManager — orchestrator
# ---------------------------------------------------------------------------
class SideMenuManager:
    """Manages the trigger bar and all slide-out panels. Non-blocking."""

    TRIGGER_WIDTH = 80
    TRIGGER_HEIGHT = 60
    TRIGGER_PADDING = 6
    PANEL_WIDTH = 380

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active_panel_key = None

        # Right edge trigger bar
        self.bar_x = screen_width - self.TRIGGER_WIDTH

        # Menu definitions: (key, label, icon, color, hover_color)
        menu_defs = [
            ("ticket_shop",      "TICKETS",  "$", (60, 120, 60),  (80, 160, 80)),
            ("upgrades",         "UPGRADES", "^", (60, 60, 120),  (80, 80, 160)),
            ("item_shop",        "ITEMS",    "!", (163, 82, 0),   (204, 102, 0)),
            ("inventory_screen", "USE",      "I", (150, 150, 30), (190, 190, 40)),
            ("ticket_inventory", "TICKETS",  "T", (100, 50, 120), (140, 70, 170)),
        ]

        self.triggers = {}
        self.panels = {}

        y = 100  # start below the HUD stat bars
        for key, label, icon, color, hover_color in menu_defs:
            trigger = SideMenuTrigger(
                self.bar_x, y,
                self.TRIGGER_WIDTH, self.TRIGGER_HEIGHT,
                label, icon, color, hover_color
            )
            panel = SideMenuPanel(
                self.PANEL_WIDTH, screen_height,
                self.bar_x,
                alpha=180,
                bg_color=color,
                title=label.title()
            )
            self.triggers[key] = trigger
            self.panels[key] = panel
            y += self.TRIGGER_HEIGHT + self.TRIGGER_PADDING

    # ---- trigger / panel lifecycle ----

    def update_triggers(self, mouse_pos, mouse_clicked):
        """Check trigger clicks. Returns key that was toggled, or None."""
        for key, trigger in self.triggers.items():
            if trigger.update(mouse_pos, mouse_clicked):
                if self.active_panel_key == key:
                    self.close_active()
                else:
                    self.open_panel(key)
                return key
        return None

    def open_panel(self, key):
        if self.active_panel_key and self.active_panel_key != key:
            self.panels[self.active_panel_key].is_open = False
            self.triggers[self.active_panel_key].active = False
        self.active_panel_key = key
        self.panels[key].is_open = True
        self.panels[key].scroll_offset = 0
        self.triggers[key].active = True

    def close_active(self):
        if self.active_panel_key:
            self.panels[self.active_panel_key].is_open = False
            self.triggers[self.active_panel_key].active = False
            self.active_panel_key = None

    def animate_all(self, dt):
        for panel in self.panels.values():
            panel.animate(dt)

    def is_point_in_menus(self, pos):
        """True if pos is over any trigger or the active open panel."""
        for trigger in self.triggers.values():
            if trigger.rect.collidepoint(pos):
                return True
        if self.active_panel_key:
            panel = self.panels[self.active_panel_key]
            if panel.contains_point(pos):
                return True
        return False

    def handle_scroll(self, scroll_y, mouse_pos):
        if self.active_panel_key:
            panel = self.panels[self.active_panel_key]
            if panel.contains_point(mouse_pos):
                panel.handle_scroll(scroll_y)

    def draw(self, screen):
        # Panels first (behind triggers)
        for panel in self.panels.values():
            panel.draw(screen)
        # Triggers on top
        for trigger in self.triggers.values():
            trigger.draw(screen)

    # ---- close button check ----

    def update_close_button(self, mouse_pos, mouse_clicked):
        """Check if the active panel's close button was clicked."""
        if not self.active_panel_key:
            return False
        panel = self.panels[self.active_panel_key]
        # Position close button for hit test
        panel.close_btn.rect.x = int(panel.current_x) + panel.panel_width - 36
        if panel.close_btn.update(mouse_pos, mouse_clicked):
            self.close_active()
            return True
        return False

    # ==================================================================
    # Content adapter methods — mirror existing popup logic
    # ==================================================================

    # ---- TICKET SHOP ----

    def setup_ticket_shop(self, ticket_types, unlocked_tickets):
        panel = self.panels["ticket_shop"]
        panel.buttons = []
        panel.desc_texts = {}
        btn_w = panel.panel_width - panel.BTN_PADDING_X * 2

        for key in ticket_types:
            config = ticket_types[key]
            is_unlocked = key in unlocked_tickets

            if is_unlocked:
                text = f"{config['name']} - ${config['cost']}"
                color = config["color"]
            else:
                text = f"??? - Earn ${config['unlock_threshold']} to unlock"
                color = (80, 80, 80)

            btn = Button(0, 0, btn_w, panel.BTN_HEIGHT, text,
                         color=color, font_size=20)
            btn.data_key = key
            btn.set_enabled(is_unlocked)
            panel.buttons.append(btn)

        panel.content_height = len(panel.buttons) * panel.BTN_SPACING
        panel._recalc_scroll()

    def update_ticket_shop(self, mouse_pos, mouse_clicked, player, ticket_types):
        panel = self.panels["ticket_shop"]
        if not panel.is_open or panel.is_animating:
            return None

        unlocked = player.get_unlocked_tickets()
        bought = None

        for btn in panel.buttons:
            key = btn.data_key
            is_unlocked = key in unlocked
            config = ticket_types[key]
            can_afford = player.can_afford(config["cost"])
            btn.set_enabled(is_unlocked and can_afford)

            if is_unlocked:
                btn.set_text(f"{config['name']} - ${config['cost']}")
                btn.color = config["color"]
            else:
                btn.set_text(f"??? - Earn ${config['unlock_threshold']} to unlock")
                btn.color = (80, 80, 80)

            if btn.update(mouse_pos, mouse_clicked):
                bought = key
        return bought

    # ---- UPGRADES ----

    def setup_upgrades(self, upgrades, player):
        panel = self.panels["upgrades"]
        panel.buttons = []
        panel.desc_texts = {}
        btn_w = panel.panel_width - panel.BTN_PADDING_X * 2

        for idx, (key, config) in enumerate(upgrades.items()):
            level = player.upgrades[key]
            cost = player.get_upgrade_cost(key)

            if cost is None:
                text = f"{config['name']} - MAX LEVEL"
            else:
                text = f"{config['name']} (Lv {level}) - ${cost}"

            btn = Button(0, 0, btn_w, panel.BTN_HEIGHT, text,
                         color=(70, 70, 110), font_size=18)
            btn.data_key = key
            btn.set_enabled(cost is not None and player.can_afford(cost))
            panel.buttons.append(btn)
            panel.desc_texts[idx] = config["description"]

        panel.content_height = len(panel.buttons) * panel.BTN_SPACING
        panel._recalc_scroll()

    def update_upgrades(self, mouse_pos, mouse_clicked, player, upgrades):
        panel = self.panels["upgrades"]
        if not panel.is_open or panel.is_animating:
            return None

        bought = None
        for idx, btn in enumerate(panel.buttons):
            key = btn.data_key
            config = upgrades[key]
            cost = player.get_upgrade_cost(key)
            level = player.upgrades[key]
            can_afford = cost is not None and player.can_afford(cost)
            btn.set_enabled(can_afford)

            if cost is None:
                btn.set_text(f"{config['name']} - MAX LEVEL")
            else:
                btn.set_text(f"{config['name']} (Lv {level}) - ${cost}")

            if btn.update(mouse_pos, mouse_clicked):
                bought = key
        return bought

    # ---- ITEM SHOP ----

    def setup_item_shop(self, items, player):
        panel = self.panels["item_shop"]
        panel.buttons = []
        panel.desc_texts = {}
        btn_w = panel.panel_width - panel.BTN_PADDING_X * 2

        idx = 0
        for key, config in items.items():
            cost = player.get_item_cost(key)
            if cost is None:
                continue  # level too low, skip entirely

            owned = player.inventory.items_in_inventory.get(key, 0)
            text = f"{config['name']} (Owned:{owned}) - ${cost}"

            btn = Button(0, 0, btn_w, panel.BTN_HEIGHT, text,
                         color=(153, 79, 0), font_size=18)
            btn.data_key = key
            btn.set_enabled(player.can_afford(cost))
            panel.buttons.append(btn)
            panel.desc_texts[idx] = config["description"]
            idx += 1

        panel.content_height = len(panel.buttons) * panel.BTN_SPACING
        panel._recalc_scroll()

    def update_item_shop(self, mouse_pos, mouse_clicked, player, items):
        panel = self.panels["item_shop"]
        if not panel.is_open or panel.is_animating:
            return None

        bought = None
        for btn in panel.buttons:
            key = btn.data_key
            config = items[key]
            cost = player.get_item_cost(key)
            owned = player.inventory.items_in_inventory.get(key, 0)
            can_afford = cost is not None and player.can_afford(cost)
            btn.set_enabled(can_afford)
            if cost is not None:
                btn.set_text(f"{config['name']} (Owned:{owned}) - ${cost}")

            if btn.update(mouse_pos, mouse_clicked):
                bought = key
        return bought

    # ---- INVENTORY (consume items) ----

    def setup_inventory(self, player):
        panel = self.panels["inventory_screen"]
        panel.buttons = []
        panel.desc_texts = {}
        btn_w = panel.panel_width - panel.BTN_PADDING_X * 2

        idx = 0
        for key, config in player.inventory.all_game_items.items():
            owned = player.inventory.items_in_inventory.get(key, 0)
            if owned <= 0:
                continue

            text = f"{config['name']} - Owned: {owned}"
            btn = Button(0, 0, btn_w, panel.BTN_HEIGHT, text,
                         color=(70, 70, 110), font_size=20)
            btn.data_key = key
            btn.set_enabled(True)
            panel.buttons.append(btn)
            panel.desc_texts[idx] = config.get("description", "")
            idx += 1

        panel.content_height = len(panel.buttons) * panel.BTN_SPACING
        panel._recalc_scroll()

    def update_inventory(self, mouse_pos, mouse_clicked, player):
        panel = self.panels["inventory_screen"]
        if not panel.is_open or panel.is_animating:
            return None

        used = None
        for btn in panel.buttons:
            key = btn.data_key
            config = player.inventory.all_game_items[key]
            owned = player.inventory.items_in_inventory.get(key, 0)
            btn.set_enabled(owned > 0)
            btn.set_text(f"{config['name']} - Owned: {owned}")

            if btn.update(mouse_pos, mouse_clicked):
                used = key
        return used

    # ---- TICKET INVENTORY ----

    def setup_ticket_inventory(self, current_ticket, ticket_queue):
        panel = self.panels["ticket_inventory"]
        panel.buttons = []
        panel.desc_texts = {}
        btn_w = panel.panel_width - panel.BTN_PADDING_X * 2

        all_tickets = []
        if current_ticket is not None:
            all_tickets.append((current_ticket, True))
        for t in ticket_queue:
            all_tickets.append((t, False))

        for i, (ticket, is_current) in enumerate(all_tickets):
            label = self._ticket_label(ticket, is_current)
            color = self._ticket_button_color(ticket, is_current)

            btn = Button(0, 0, btn_w, 50, label,
                         color=color, font_size=17)
            btn.data_ref = ticket
            if is_current:
                btn.set_enabled(False)
            panel.buttons.append(btn)

        panel.content_height = len(panel.buttons) * panel.BTN_SPACING
        panel._recalc_scroll()

    def update_ticket_inventory(self, mouse_pos, mouse_clicked,
                                current_ticket, ticket_queue):
        panel = self.panels["ticket_inventory"]
        if not panel.is_open or panel.is_animating:
            return None

        clicked = None
        for btn in panel.buttons:
            if btn.update(mouse_pos, mouse_clicked):
                clicked = btn.data_ref
        return clicked

    # ---- helpers ----

    @staticmethod
    def _ticket_label(ticket, is_current):
        config = ticket.config
        name = config["name"]
        if ticket.is_complete():
            status = "DONE - Collect!"
        elif hasattr(ticket, 'cells_revealed'):
            revealed = ticket.get_cells_revealed_count()
            status = f"{revealed}/9 revealed"
        elif ticket.scratched:
            pct = int(ticket.scratch_percent * 100)
            status = f"{pct}% scratched"
        else:
            status = "Unscratched"
        prefix = "[ACTIVE] " if is_current else ""
        return f"{prefix}{name} - {status}"

    @staticmethod
    def _ticket_button_color(ticket, is_current):
        if is_current:
            return (80, 80, 50)
        elif ticket.is_complete():
            return (60, 120, 60)
        elif ticket.scratched:
            return (100, 80, 60)
        else:
            r, g, b = ticket.config["color"]
            return (max(0, r - 40), max(0, g - 40), max(0, b - 40))
