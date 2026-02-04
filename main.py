import pygame
import sys
import random

from game.ticket import ScratchTicket, TICKET_TYPES
from game.player import Player, UPGRADES
from game.ui import HUD, MessagePopup, TicketShopUI, UpgradeShopUI, Button
from game.particles import ParticleSystem, ScreenShake

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Colors
BG_COLOR = (40, 45, 60)
GAS_STATION_COLOR = (70, 80, 90)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Scratch-Off Ticket Idle Game")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.player = Player()
        self.current_ticket = None
        self.ticket_queue = []  # For bulk buying

        # UI
        self.hud = HUD(SCREEN_WIDTH)
        self.messages = MessagePopup()

        # Ticket shop on the left
        self.ticket_shop = TicketShopUI(20, 120, 200, 280)
        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())

        # Upgrade shop on the left, below ticket shop
        self.upgrade_shop = UpgradeShopUI(20, 420, 200, 260)
        self.upgrade_shop.setup_buttons(UPGRADES, self.player)

        # Collect winnings button
        self.collect_button = Button(
            SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 80,
            150, 50, "COLLECT",
            color=(80, 180, 80), hover_color=(100, 220, 100)
        )
        self.collect_button.set_enabled(False)

        # Effects
        self.particles = ParticleSystem()
        self.screen_shake = ScreenShake()

        # State
        self.scratching = False
        self.pending_prize = 0
        self.auto_scratch_timer = 0

        # Draw background once
        self.background = self._create_background()

    def _create_background(self):
        """Create the gas station background."""
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(BG_COLOR)

        # Gas station counter area
        counter_rect = pygame.Rect(240, 50, SCREEN_WIDTH - 260, SCREEN_HEIGHT - 100)
        pygame.draw.rect(bg, GAS_STATION_COLOR, counter_rect, border_radius=20)
        pygame.draw.rect(bg, (90, 100, 110), counter_rect, 4, border_radius=20)

        # Scratching area indicator
        scratch_area = pygame.Rect(280, 100, 400, 300)
        pygame.draw.rect(bg, (50, 55, 70), scratch_area, border_radius=15)
        pygame.draw.rect(bg, (80, 85, 100), scratch_area, 2, border_radius=15)

        # Title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("GAS STATION LOTTO", True, (255, 200, 100))
        bg.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 50, 60))

        # Instructions
        inst_font = pygame.font.Font(None, 24)
        instructions = [
            "Buy tickets from the shop",
            "Click and drag to scratch",
            "Win money and upgrade!",
        ]
        y = SCREEN_HEIGHT - 60
        for inst in instructions:
            text = inst_font.render(inst, True, (150, 150, 170))
            bg.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2 + 50, y))
            y += 20

        return bg

    def buy_ticket(self, ticket_type):
        """Buy a ticket of the given type."""
        config = TICKET_TYPES[ticket_type]
        if self.player.spend(config["cost"]):
            # Create new ticket centered in the scratch area
            ticket = ScratchTicket(
                ticket_type,
                SCREEN_WIDTH // 2 - 120,  # Center X
                150,  # Y position
                300, 200,
                luck_bonus=self.player.get_luck_bonus()
            )

            if self.current_ticket is None:
                self.current_ticket = ticket
            else:
                self.ticket_queue.append(ticket)

            self.collect_button.set_enabled(False)
            self.player.save_game()
            return True
        return False

    def handle_scratch(self, mouse_pos):
        """Handle scratching the current ticket."""
        if self.current_ticket and not self.current_ticket.is_complete():
            radius = self.player.get_scratch_radius()
            result = self.current_ticket.scratch(mouse_pos[0], mouse_pos[1], radius)

            if result:
                # Add scratch particles
                self.particles.add_scratch_particles(
                    result["x"], result["y"], result["color"], count=3
                )

            # Check if ticket is now complete
            if self.current_ticket.is_complete():
                self._handle_ticket_complete()

    def _handle_ticket_complete(self):
        """Handle when a ticket is fully scratched."""
        prize = self.current_ticket.get_prize()
        self.pending_prize = prize
        self.player.scratch_ticket()

        if prize > 0:
            # Win!
            self.messages.add_message(f"WIN ${prize}!", (100, 255, 100))

            # Particles based on win size
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
            self.messages.add_message("Try again!", (255, 150, 100))

        self.collect_button.set_enabled(True)

    def collect_winnings(self):
        """Collect winnings from completed ticket."""
        if self.pending_prize > 0:
            self.player.earn(self.pending_prize)
            self.messages.add_message(f"+${self.pending_prize}", (100, 255, 100), 1.0,flag="AMOUNT_TEXT")
            self.pending_prize = 0

        # Move to next ticket in queue or clear
        if self.ticket_queue:
            self.current_ticket = self.ticket_queue.pop(0)
            self.collect_button.set_enabled(False)
        else:
            self.current_ticket = None

        self.collect_button.set_enabled(False)
        self.player.save_game()

        # Update shop buttons
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

            # Scratch at a random position on the ticket
            ticket = self.current_ticket
            x = ticket.x + random.randint(30, ticket.width - 30)
            y = ticket.y + random.randint(50, ticket.height - 30)

            self.handle_scratch((x, y))

    def update(self, dt):
        """Update game state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Handle scratching
        if mouse_pressed and self.current_ticket and not self.current_ticket.is_complete():
            self.handle_scratch(mouse_pos)

        # Auto scratch
        self.auto_scratch(dt)

        # Update ticket shop
        bought_ticket = self.ticket_shop.update(
            mouse_pos, mouse_pressed and not self.scratching,
            self.player, TICKET_TYPES
        )
        if bought_ticket:
            bulk = self.player.get_bulk_amount()
            for _ in range(bulk):
                if not self.buy_ticket(bought_ticket):
                    break

        # Update upgrade shop
        bought_upgrade = self.upgrade_shop.update(
            mouse_pos, mouse_pressed and not self.scratching,
            self.player, UPGRADES
        )
        if bought_upgrade:
            if self.player.buy_upgrade(bought_upgrade):
                upgrade_name = UPGRADES[bought_upgrade]["name"]
                self.messages.add_message(f"{upgrade_name} upgraded!", (150, 150, 255))
                self.upgrade_shop.setup_buttons(UPGRADES, self.player)

        # Update collect button
        if self.current_ticket and self.current_ticket.is_complete():
            self.collect_button.set_enabled(True)
            if self.collect_button.update(mouse_pos, mouse_pressed):
                self.collect_winnings()
        else:
            self.collect_button.set_enabled(False)

        # Update effects
        self.particles.update(dt)
        self.screen_shake.update(dt)
        self.messages.update(dt)

        self.scratching = mouse_pressed

    def draw(self):
        """Draw the game."""
        # Apply screen shake
        shake_offset = self.screen_shake.get_offset()

        # Draw background
        self.screen.blit(self.background, shake_offset)

        # Draw current ticket
        if self.current_ticket:
            # Offset for shake
            orig_x, orig_y = self.current_ticket.x, self.current_ticket.y
            self.current_ticket.x += shake_offset[0]
            self.current_ticket.y += shake_offset[1]
            self.current_ticket.draw(self.screen)
            self.current_ticket.x, self.current_ticket.y = orig_x, orig_y

            # Show queue count
            if self.ticket_queue:
                font = pygame.font.Font(None, 24)
                queue_text = font.render(f"+{len(self.ticket_queue)} more", True, (200, 200, 200))
                self.screen.blit(queue_text, (
                    self.current_ticket.x + self.current_ticket.width // 2 - queue_text.get_width() // 2,
                    self.current_ticket.y + self.current_ticket.height + 10
                ))

        # Draw UI
        self.ticket_shop.draw(self.screen)
        self.upgrade_shop.draw(self.screen)
        self.hud.draw(self.screen, self.player)

        # Draw collect button if applicable
        if self.current_ticket and self.current_ticket.is_complete():
            self.collect_button.draw(self.screen)

        # Draw particles (on top of everything)
        self.particles.draw(self.screen)

        # Draw messages

        self.messages.draw(self.screen, SCREEN_WIDTH // 2 + 50, 300)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        # Reset game (debug)
                        self.player.reset_game()
                        self.current_ticket = None
                        self.ticket_queue = []
                        self.pending_prize = 0
                        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())
                        self.upgrade_shop.setup_buttons(UPGRADES, self.player)
                        self.messages.add_message("Game Reset!", (255, 100, 100))

            self.update(dt)
            self.draw()

        # Save on exit
        self.player.save_game()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
