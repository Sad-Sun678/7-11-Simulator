import pygame
import sys
import random

from game.ticket import ScratchTicket, TICKET_TYPES, create_ticket
from game.player import Player, UPGRADES
from game.ui import (HUD, MessagePopup, TicketShopPopup, UpgradeShopPopup,
                     MainMenuButtons, AutoCollectTimer,HealthBar)
from game.particles import ParticleSystem, ScreenShake

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60

# Colors
BG_COLOR = (35, 40, 50)
COUNTER_COLOR = (55, 60, 70)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gas Station Lotto")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.player = Player()
        self.current_ticket = None
        self.ticket_queue = []

        # UI - Popup menus
        self.ticket_shop = TicketShopPopup(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())

        self.upgrade_shop = UpgradeShopPopup(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.upgrade_shop.setup_buttons(UPGRADES, self.player)

        # Main screen buttons
        self.main_buttons = MainMenuButtons(SCREEN_WIDTH, SCREEN_HEIGHT)

        # HUD and messages
        self.hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.messages = MessagePopup()
        self.auto_collect_timer_ui = AutoCollectTimer()
        self.health_bar = HealthBar(SCREEN_WIDTH//2 + 680,SCREEN_HEIGHT//2 - 250,15,self.player.morale,"MORALE")

        # Effects
        self.particles = ParticleSystem()
        self.screen_shake = ScreenShake()

        # State
        self.scratching = False
        self.pending_prize = 0
        self.auto_scratch_timer = 0
        self.auto_collect_timer = 0
        self.auto_collect_total_time = None

        # Track mouse state for click detection
        self.mouse_was_pressed = False

        # Create background
        self.background = self._create_background()

    def _create_background(self):
        """Create the gas station counter background."""
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(BG_COLOR)

        # Main counter area (where tickets go)
        counter_rect = pygame.Rect(50, 80, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 180)
        pygame.draw.rect(bg, COUNTER_COLOR, counter_rect, border_radius=20)
        pygame.draw.rect(bg, (75, 80, 90), counter_rect, 4, border_radius=20)

        # Scratching mat area
        mat_rect = pygame.Rect(100, 120, SCREEN_WIDTH - 300, SCREEN_HEIGHT - 280)
        pygame.draw.rect(bg, (45, 50, 60), mat_rect, border_radius=15)
        pygame.draw.rect(bg, (65, 70, 80), mat_rect, 2, border_radius=15)

        # "Scratch here" text when no ticket
        font = pygame.font.Font(None, 32)
        hint_text = font.render("Buy a ticket to start!", True, (80, 85, 95))
        bg.blit(hint_text, (SCREEN_WIDTH // 2 - hint_text.get_width() // 2,
                           SCREEN_HEIGHT // 2 - hint_text.get_height() // 2))

        return bg

    def buy_ticket(self, ticket_type):
        """Buy a ticket of the given type."""
        config = TICKET_TYPES[ticket_type]
        if self.player.spend(config["cost"]):
            # Create new ticket centered on the counter
            ticket = create_ticket(
                ticket_type,
                SCREEN_WIDTH // 2 - 170,  # Center X (account for ticket width)
                SCREEN_HEIGHT // 2 - 180,  # Center Y
                340, 280,
                luck_bonus=self.player.get_luck_bonus()
            )

            if self.current_ticket is None:
                self.current_ticket = ticket
                self.auto_collect_timer = 0  # Reset auto-collect timer
            else:
                self.ticket_queue.append(ticket)

            self.player.save_game()
            return True
        return False

    def handle_scratch(self, mouse_pos):
        """Handle scratching the current ticket."""
        if self.current_ticket and not self.current_ticket.is_complete():
            radius = self.player.get_scratch_radius()
            result = self.current_ticket.scratch(mouse_pos[0], mouse_pos[1], radius)

            if result:
                self.particles.add_scratch_particles(
                    result["x"], result["y"], result["color"], count=3
                )

            if self.current_ticket.is_complete():
                self._handle_ticket_complete()

    def _handle_ticket_complete(self):
        """Handle when a ticket is fully scratched."""
        prize = self.current_ticket.get_prize()
        self.pending_prize = prize
        self.player.scratch_ticket()

        # Reset auto-collect timer
        self.auto_collect_timer = 0
        self.auto_collect_total_time = self.player.get_auto_collect_delay()

        if prize > 0:
            self.messages.add_message(f"WIN ${prize}!", (100, 255, 100), flag="WIN_PRIZE")

            ticket_center_x = self.current_ticket.x + self.current_ticket.width // 2
            ticket_center_y = self.current_ticket.y + self.current_ticket.height // 2

            if prize >= 100:
                self.particles.add_big_win_particles(ticket_center_x, ticket_center_y, prize)
                self.screen_shake.shake(15, 0.5)
            elif prize >= 25:
                self.particles.add_win_particles(ticket_center_x, ticket_center_y, prize, 50)
                self.screen_shake.shake(8, 0.3)
            else:
                self.particles.add_win_particles(ticket_center_x, ticket_center_y, prize, 20)
                self.screen_shake.shake(3, 0.15)
        else:
            self.messages.add_message("Try again!", (255, 150, 100), flag="TRY_AGAIN")

        self.main_buttons.set_collect_enabled(True)

    def collect_winnings(self):
        """Collect winnings from completed ticket."""
        if self.pending_prize > 0:
            self.player.earn(self.pending_prize)
            self.messages.add_message(f"+${self.pending_prize}", (100, 255, 100), 1.0, flag="AMOUNT_TEXT")
            self.pending_prize = 0

        # Move to next ticket or clear
        if self.ticket_queue:
            self.current_ticket = self.ticket_queue.pop(0)
            self.auto_collect_timer = 0
            self.auto_collect_total_time = None
        else:
            self.current_ticket = None

        self.main_buttons.set_collect_enabled(False)
        self.player.save_game()

        # Update shop buttons for unlocks
        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())

    def auto_scratch(self, dt):
        """Handle auto-scratching if upgrade is purchased."""
        speed = self.player.get_auto_scratch_speed()
        if speed == 0 or self.current_ticket is None or self.current_ticket.is_complete():
            return

        self.auto_scratch_timer += dt
        interval = 1.0 / speed

        while self.auto_scratch_timer >= interval:
            self.auto_scratch_timer -= interval

            ticket = self.current_ticket
            x = ticket.x + random.randint(30, ticket.width - 30)
            y = ticket.y + random.randint(50, ticket.height - 30)

            self.handle_scratch((x, y))

    def auto_collect(self, dt):
        """Handle auto-collecting if upgrade is purchased."""
        if self.current_ticket is None or not self.current_ticket.is_complete():
            return

        delay = self.player.get_auto_collect_delay()
        if delay is None:
            return

        self.auto_collect_timer += dt

        if self.auto_collect_timer >= delay:
            self.collect_winnings()

    def update(self, dt):
        """Update game state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Detect click (mouse down this frame, wasn't down last frame)
        mouse_clicked = mouse_pressed and not self.mouse_was_pressed

        # Check if any popup is open
        popup_open = self.ticket_shop.is_open or self.upgrade_shop.is_open

        # Handle popup menus first (they block other interactions)
        if self.ticket_shop.is_open:
            bought_ticket = self.ticket_shop.update(mouse_pos, mouse_clicked, self.player, TICKET_TYPES)
            if bought_ticket:
                bulk = self.player.get_bulk_amount()
                for _ in range(bulk):
                    if not self.buy_ticket(bought_ticket):
                        break

        elif self.upgrade_shop.is_open:
            bought_upgrade = self.upgrade_shop.update(mouse_pos, mouse_clicked, self.player, UPGRADES)
            if bought_upgrade:
                if self.player.buy_upgrade(bought_upgrade):
                    upgrade_name = UPGRADES[bought_upgrade]["name"]
                    self.messages.add_message(f"{upgrade_name} upgraded!", (150, 150, 255))
                    self.upgrade_shop.setup_buttons(UPGRADES, self.player)

        else:
            # No popup open - handle main game

            # Handle scratching (continuous while mouse is held)
            if mouse_pressed and self.current_ticket and not self.current_ticket.is_complete():
                self.handle_scratch(mouse_pos)

            # Handle main menu button clicks
            button_clicks = self.main_buttons.update(mouse_pos, mouse_clicked)

            if button_clicks["ticket_shop"]:
                self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())
                self.ticket_shop.open()
            elif button_clicks["upgrades"]:
                self.upgrade_shop.setup_buttons(UPGRADES, self.player)
                self.upgrade_shop.open()
            elif button_clicks["collect"]:
                self.collect_winnings()

            # Update collect button state
            if self.current_ticket and self.current_ticket.is_complete():
                self.main_buttons.set_collect_enabled(True)
            else:
                self.main_buttons.set_collect_enabled(False)

        # Auto mechanics (always run)
        self.auto_scratch(dt)
        self.auto_collect(dt)

        # Update effects
        self.particles.update(dt)
        self.screen_shake.update(dt)
        self.messages.update(dt)
        self.health_bar.update(self.player.morale)

        self.mouse_was_pressed = mouse_pressed

    def draw(self):
        """Draw the game."""
        shake_offset = self.screen_shake.get_offset()

        # Draw background
        self.screen.blit(self.background, shake_offset)

        # Draw current ticket
        if self.current_ticket:
            orig_x, orig_y = self.current_ticket.x, self.current_ticket.y
            self.current_ticket.x += shake_offset[0]
            self.current_ticket.y += shake_offset[1]
            self.current_ticket.draw(self.screen)
            self.current_ticket.x, self.current_ticket.y = orig_x, orig_y

            # Show queue count
            if self.ticket_queue:
                font = pygame.font.Font(None, 24)
                queue_text = font.render(f"+{len(self.ticket_queue)} more tickets", True, (180, 180, 180))
                self.screen.blit(queue_text, (
                    self.current_ticket.x + self.current_ticket.width // 2 - queue_text.get_width() // 2,
                    self.current_ticket.y + self.current_ticket.height + 15
                ))

            # Show auto-collect timer if applicable
            if self.current_ticket.is_complete() and self.auto_collect_total_time is not None:
                time_remaining = max(0, self.auto_collect_total_time - self.auto_collect_timer)
                self.auto_collect_timer_ui.draw(
                    self.screen,
                    self.current_ticket.x + self.current_ticket.width // 2,
                    self.current_ticket.y + self.current_ticket.height + 40,
                    time_remaining,
                    self.auto_collect_total_time
                )

        # Draw HUD
        self.hud.draw(self.screen, self.player)
        # TODO DRAW HEALTHBAR
        self.health_bar.draw(self.screen)
        # Draw main buttons
        self.main_buttons.draw(self.screen)

        # Draw particles
        self.particles.draw(self.screen)

        # Draw messages
        self.messages.draw(self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Draw popup menus (on top of everything)
        self.ticket_shop.draw(self.screen)
        self.upgrade_shop.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEWHEEL:
                    if self.upgrade_shop.is_in_scroll_area(pygame.mouse.get_pos()):
                        self.upgrade_shop.handle_scroll(event.y)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Close popups first, then exit
                        if self.ticket_shop.is_open:
                            self.ticket_shop.close()
                        elif self.upgrade_shop.is_open:
                            self.upgrade_shop.close()
                        else:
                            self.running = False
                    elif event.key == pygame.K_r:
                        # Reset game (debug)
                        self.player.reset_game()
                        self.current_ticket = None
                        self.ticket_queue = []
                        self.pending_prize = 0
                        self.auto_collect_timer = 0
                        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())
                        self.upgrade_shop.setup_buttons(UPGRADES, self.player)
                        self.messages.add_message("Game Reset!", (255, 100, 100))
                    elif event.key == pygame.K_d:
                        print("D")
                        self.player.morale -= 10

            self.update(dt)
            self.draw()

        self.player.save_game()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
