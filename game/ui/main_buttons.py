from game.ui.button import Button


class MainMenuButtons:
    """The main screen buttons to open shops."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        btn_width = 160
        btn_height = 50
        padding = 20

        btn_y = screen_height - btn_height - padding

        # CHANGE THESE TWO VALUES TO MOVE THE WHOLE CLUSTER
        self.cluster_x = 500
        self.cluster_y = -100

        self.ticket_shop_btn = Button(
            padding, btn_y,
            btn_width, btn_height,
            "TICKETS",
            color=(60, 120, 60), hover_color=(80, 160, 80), font_size=28
        )

        self.upgrades_btn = Button(
            padding + btn_width + 10, btn_y,
            btn_width, btn_height,
            "UPGRADES",
            color=(60, 60, 120), hover_color=(80, 80, 160), font_size=28
        )

        self.item_shop_btn = Button(
            padding + btn_width + 180, btn_y,
            btn_width, btn_height,
            "Item Shop",
            color=(204, 102, 0), hover_color=(255, 128, 0), font_size=28
        )

        self.inventory_btn = Button(
            padding + btn_width + 350, btn_y,
            btn_width, btn_height,
            "Inventory",
            color=(204, 204, 0), hover_color=(255, 255, 0), font_size=28
        )

        self.ticket_inventory_btn = Button(
            padding + btn_width + 520, btn_y,
            btn_width, btn_height,
            "MY TICKETS",
            color=(120, 60, 140), hover_color=(160, 80, 180), font_size=24
        )

        self.collect_btn = Button(
            padding + btn_width + 115, btn_y - 70,
            150, btn_height-10,
            "COLLECT",
            color=(120, 160, 60), hover_color=(160, 200, 80),
            font_size=28
        )

        self.collect_btn.set_enabled(False)

        self.pee_btn = Button(
            375, 900,
            120, btn_height-10,
            "Go Piss",
            color=(200, 180, 50), hover_color=(240, 220, 80),
            font_size=28
        )

        self.pee_btn.set_enabled(False)

        self._buttons = [
            self.ticket_shop_btn,
            self.upgrades_btn,
            self.item_shop_btn,
            self.inventory_btn,
            self.ticket_inventory_btn,
            self.collect_btn,
            self.pee_btn
        ]

        # Apply cluster offset immediately
        for btn in self._buttons:
            btn.set_pos(btn.rect.x + self.cluster_x,
                        btn.rect.y + self.cluster_y)

    def update(self, mouse_pos, mouse_clicked):
        return {
            "ticket_shop": self.ticket_shop_btn.update(mouse_pos, mouse_clicked),
            "upgrades": self.upgrades_btn.update(mouse_pos, mouse_clicked),
            "collect": self.collect_btn.update(mouse_pos, mouse_clicked),
            "item_shop": self.item_shop_btn.update(mouse_pos, mouse_clicked),
            "inventory_screen": self.inventory_btn.update(mouse_pos, mouse_clicked),
            "ticket_inventory": self.ticket_inventory_btn.update(mouse_pos, mouse_clicked),
            "pee": self.pee_btn.update(mouse_pos, mouse_clicked)
        }

    def set_collect_enabled(self, enabled):
        self.collect_btn.set_enabled(enabled)

    def set_pee_enabled(self, enabled):
        self.pee_btn.set_enabled(enabled)

    def draw(self, screen):
        self.ticket_shop_btn.draw(screen)
        self.upgrades_btn.draw(screen)
        self.item_shop_btn.draw(screen)
        self.inventory_btn.draw(screen)
        self.ticket_inventory_btn.draw(screen)

        if self.collect_btn.enabled:
            self.collect_btn.draw(screen)
        if self.pee_btn.enabled:
            self.pee_btn.draw(screen)
