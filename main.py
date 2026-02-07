import pygame
import sys
import random
import math

from game.config import TICKET_TYPES, UPGRADES, ITEMS, LEVEL_CONFIG, PEE_CONFIG, load_symbol_images, load_ticket_images
from game.ticket import ScratchTicket, create_ticket
from game.player import Player
from game.ui import (HUD, MessagePopup, TicketShopPopup, UpgradeShopPopup,
                     MainMenuButtons, AutoCollectTimer, ItemShopPopup, InventoryPopup,
                     StatBar, Cigarette, TicketInventoryPopup, PeeCam, SideMenuManager)
from game.effects import DrunkEffect
from game.particles import ParticleSystem, ScreenShake
from game.pee_minigame import PeeMinigame
from game.ticket_mat import TicketMatManager

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1800
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

        # Load images now that display exists
        load_symbol_images()
        load_ticket_images()

        # Game objects
        self.player = Player()

        # Multi-ticket mat system (replaces single current_ticket + ticket_queue)
        self.mat = TicketMatManager()

        # UI - Popup menus (kept as reference, no longer opened)
        self.ticket_shop = TicketShopPopup(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())

        self.upgrade_shop = UpgradeShopPopup(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.upgrade_shop.setup_buttons(UPGRADES, self.player)

        self.item_shop = ItemShopPopup(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.inventory_screen = InventoryPopup(SCREEN_WIDTH,SCREEN_HEIGHT)

        self.ticket_inventory = TicketInventoryPopup(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Main screen buttons (PEE still used)
        self.main_buttons = MainMenuButtons(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Side menu system (non-blocking replacement for popup menus)
        self.side_menus = SideMenuManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # HUD and messages
        self.hud = HUD(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.messages = MessagePopup()
        self.auto_collect_timer_ui = AutoCollectTimer()
        self.hunger_bar = StatBar(self.player,50,50,200,25,("current_hunger","max_hunger"))
        self.morale_bar = StatBar(self.player,50,80,200,25,("morale","morale_cap"),color=(0,76,153))
        self.xp_bar = StatBar(self.player,50,110,200,25,("current_xp","xp_to_next_level"),color=(180,140,50))
        self.pee_bar = StatBar(self.player,50,140,200,25,("current_bladder","max_bladder"),color=(255,255,0))
        self.level_font = pygame.font.Font(None, 22)
        # Effects
        self.particles = ParticleSystem()
        self.screen_shake = ScreenShake()
        # Drunk effect (debug)
        self.drunk = DrunkEffect()
        # Cigarette
        self.cig_idle = pygame.image.load("assets/sprites/cig_idle.png").convert_alpha()
        self.cig_smoking = pygame.image.load("assets/sprites/cig_smoking.png").convert_alpha()

        self.cigarette = Cigarette(
            self.cig_idle,
            self.cig_smoking,
            1500, 420,
            scale=2.0,
            particle_system=self.particles
        )

        # Pee minigame
        self.pee_minigame = PeeMinigame(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.pee_minigame_active = False

        # Pee accident cam (plays when bladder full for too long)
        self.pee_cam = PeeCam(
            "assets/animation/pee_cam_spritesheet.png",
            x=50, y=420,
            frame_size=128,
            scale=2.0,
            animation_speed=0.5
        )
        self.pee_accident_timer = 0.0  # counts up while bladder is full
        self.pee_accident_active = False

        # State
        self.scratching = False
        self.auto_scratch_timer = 0
        self.auto_collect_timer = 0
        self.game_lost = False

        # Track mouse state for click detection
        self.mouse_was_pressed = False

        # Create background
        self.background = self._create_background()
        # Debug variable

    def _create_background(self):
        """Create static background."""

        # LOAD pixel art background instead of drawing it
        bg_image = pygame.image.load("assets/background/temp_bg.png").convert()
        bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        return bg

    def buy_ticket(self, ticket_type):
        """Buy a ticket of the given type."""
        config = TICKET_TYPES[ticket_type]
        if self.player.spend(config["cost"]):
            # Create ticket — position doesn't matter, mat will set it during deal anim
            ticket = create_ticket(
                ticket_type,
                0, 0,
                340, 280,
                luck_bonus=self.player.get_luck_bonus()
            )
            self.mat.add_ticket(ticket)
            self.player.save_game()
            return True
        return False

    def handle_scratch(self, mouse_pos, ticket=None):
        """Scratch the given ticket (or auto-detected from mouse position).
        Only the topmost ticket at the point can be scratched (z-order blocking)."""
        if ticket is None:
            ticket = self.mat.get_ticket_at_point(mouse_pos)
        if ticket is None or ticket.is_complete():
            return

        # Promote to top so the ticket being scratched draws on top
        self.mat._promote_to_top(ticket)

        radius = self.player.get_scratch_radius()

        mx, my = mouse_pos

        # Same offsets used in draw()
        shake_offset = self.screen_shake.get_offset()

        if self.drunk.enabled:
            drunk_offset = self.drunk.get_offset()
            ticket_offset = self.drunk.get_ticket_offset()

            mx -= (shake_offset[0] + drunk_offset[0]) * 0.4 + ticket_offset[0]
            my -= (shake_offset[1] + drunk_offset[1]) * 0.4 + ticket_offset[1]
        else:
            mx -= shake_offset[0]
            my -= shake_offset[1]

        result = ticket.scratch(mx, my, radius)

        if result:
            self.particles.add_scratch_particles(
                result["x"], result["y"], result["color"], count=3
            )
            # XP only when actually revealing new area
            if result.get("new_reveal"):
                if self.player.gain_xp(LEVEL_CONFIG["xp_sources"]["scratch_per_cell"]):
                    self.messages.add_message(f"LEVEL UP! Lv.{self.player.player_level}", (255, 255, 100))

        if ticket.is_complete():
            self._handle_ticket_complete(ticket)

    def _handle_ticket_complete(self, ticket):
        """Handle when a ticket is fully scratched."""
        prize = ticket.get_prize()
        self.player.scratch_ticket()

        # XP for completing a ticket
        leveled = self.player.gain_xp(LEVEL_CONFIG["xp_sources"]["ticket_complete"])
        if prize > 0:
            leveled = self.player.gain_xp(LEVEL_CONFIG["xp_sources"]["winner_bonus"]) or leveled
        if leveled:
            self.messages.add_message(f"LEVEL UP! Lv.{self.player.player_level}", (255, 255, 100))

        if prize > 0:
            self.messages.add_message(f"WIN ${prize}! Drag to redeem!", (100, 255, 100), flag="WIN_PRIZE")

            ticket_center_x = ticket.x + ticket.width // 2
            ticket_center_y = ticket.y + ticket.height // 2

            # $1000+ JACKPOT
            if prize >= 1000:
                self.particles.add_big_win_particles(ticket_center_x, ticket_center_y, prize)
                self.screen_shake.shake(48, 1.2)
                self.player.gain_morale(400)

            # $500+
            elif prize >= 500:
                self.particles.add_big_win_particles(ticket_center_x, ticket_center_y, prize)
                self.screen_shake.shake(40, 0.9)
                self.player.gain_morale(250)

            # $250+
            elif prize >= 250:
                self.particles.add_big_win_particles(ticket_center_x, ticket_center_y, prize)
                self.screen_shake.shake(32, 0.7)
                self.player.gain_morale(180)

            # $100+
            elif prize >= 100:
                self.particles.add_big_win_particles(ticket_center_x, ticket_center_y, prize)
                self.screen_shake.shake(22, 0.55)
                self.player.gain_morale(120)

            # $50+
            elif prize >= 50:
                self.particles.add_win_particles(ticket_center_x, ticket_center_y, prize, 80)
                self.screen_shake.shake(14, 0.4)
                self.player.gain_morale(70)

            # $25+
            elif prize >= 25:
                self.particles.add_win_particles(ticket_center_x, ticket_center_y, prize, 50)
                self.screen_shake.shake(8, 0.3)
                self.player.gain_morale(50)

            # Small wins
            else:
                self.particles.add_win_particles(ticket_center_x, ticket_center_y, prize, 20)
                self.screen_shake.shake(4, 0.18)
                self.player.gain_morale(15)

        else:
            self.messages.add_message("Try again!", (255, 150, 100), flag="TRY_AGAIN")
            self.player.lose_morale(5)
            # Loser ticket — auto-dissolve (fade out and remove)
            self.mat.dissolve_ticket(ticket)
            return

    def _redeem_ticket(self, ticket):
        """Redeem a completed ticket dropped on the redeem box."""
        prize = ticket.get_prize()
        if prize > 0:
            self.player.earn(prize)
            self.messages.add_message(f"+${prize}", (100, 255, 100), 1.0, flag="AMOUNT_TEXT")

        self.mat.remove_ticket(ticket)
        self.player.save_game()

        # Update shop buttons for unlocks
        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())

    def _stash_ticket(self, ticket):
        """Stash a ticket to the ticket inventory (shrink+fly)."""
        self.mat.stash_ticket(ticket)
        self.messages.add_message("Ticket stashed!", (180, 150, 220))

    def auto_scratch(self, dt):
        """Handle auto-scratching if upgrade is purchased."""
        speed = self.player.get_auto_scratch_speed()
        target = self.mat.auto_scratch_target()
        if speed == 0 or target is None:
            return

        self.auto_scratch_timer += dt
        interval = 1.0 / speed

        while self.auto_scratch_timer >= interval:
            self.auto_scratch_timer -= interval

            # Re-check target each scratch (might have completed)
            target = self.mat.auto_scratch_target()
            if target is None:
                break

            x = target.x + random.randint(30, target.width - 30)
            y = target.y + random.randint(50, target.height - 30)

            self.handle_scratch((x, y), ticket=target)

    def auto_collect(self, dt):
        """Handle auto-collecting: auto-redeem first completed winner on mat."""
        delay = self.player.get_auto_collect_delay()
        if delay is None:
            return

        winner = self.mat.get_first_complete_winner()
        if winner is None:
            self.auto_collect_timer = 0
            return

        self.auto_collect_timer += dt

        if self.auto_collect_timer >= delay:
            self.auto_collect_timer = 0
            self._redeem_ticket(winner)
    def check_for_lose_condition(self):
        if self.player.morale <= 0:
            self.game_lost = True
        else:
            return
    # ------ Side menu helpers ------

    def _setup_side_panel(self, key):
        """Populate the side panel that was just opened."""
        if key == "ticket_shop":
            self.side_menus.setup_ticket_shop(TICKET_TYPES, self.player.get_unlocked_tickets())
        elif key == "upgrades":
            self.side_menus.setup_upgrades(UPGRADES, self.player)
        elif key == "item_shop":
            self.side_menus.setup_item_shop(ITEMS, self.player)
        elif key == "inventory_screen":
            self.side_menus.setup_inventory(self.player)
        elif key == "ticket_inventory":
            self.side_menus.setup_ticket_inventory(
                self.mat.mat_tickets, self.mat.ticket_queue, self.mat.stashed_tickets)

    def _update_active_panel(self, mouse_pos, mouse_clicked):
        """Update the active side panel's content. Returns (key, result) or None."""
        active = self.side_menus.active_panel_key
        if active is None:
            return None
        result = None
        if active == "ticket_shop":
            result = self.side_menus.update_ticket_shop(mouse_pos, mouse_clicked, self.player, TICKET_TYPES)
        elif active == "upgrades":
            result = self.side_menus.update_upgrades(mouse_pos, mouse_clicked, self.player, UPGRADES)
        elif active == "item_shop":
            result = self.side_menus.update_item_shop(mouse_pos, mouse_clicked, self.player, ITEMS)
        elif active == "inventory_screen":
            result = self.side_menus.update_inventory(mouse_pos, mouse_clicked, self.player)
        elif active == "ticket_inventory":
            result = self.side_menus.update_ticket_inventory(
                mouse_pos, mouse_clicked,
                self.mat.mat_tickets, self.mat.ticket_queue, self.mat.stashed_tickets)
        if result is not None:
            return (active, result)
        return None

    def _handle_panel_result(self, result):
        """Apply the action from a side panel interaction."""
        key, value = result
        if key == "ticket_shop":
            bulk = self.player.get_bulk_amount()
            for _ in range(bulk):
                if not self.buy_ticket(value):
                    break
            # Refresh panel
            self.side_menus.setup_ticket_shop(TICKET_TYPES, self.player.get_unlocked_tickets())
        elif key == "upgrades":
            if self.player.buy_upgrade(value):
                upgrade_name = UPGRADES[value]["name"]
                self.messages.add_message(f"{upgrade_name} upgraded!", (150, 150, 255))
                self.side_menus.setup_upgrades(UPGRADES, self.player)
        elif key == "item_shop":
            if self.player.buy_item(value):
                item_name = ITEMS[value]['name']
                self.messages.add_message(f"{item_name} purchased!", (150, 150, 255))
                self.side_menus.setup_item_shop(ITEMS, self.player)
        elif key == "inventory_screen":
            if self.player.try_use_item(value):
                self.player.consume_item(value)
                self.messages.add_message(f"{value.title()} Consumed!")
                self.side_menus.setup_inventory(self.player)
        elif key == "ticket_inventory":
            # Stashed ticket pulled out — unstash and start dragging
            self.mat.unstash_ticket(value, pygame.mouse.get_pos())
            self.side_menus.close_active()
            self.side_menus.setup_ticket_inventory(
                self.mat.mat_tickets, self.mat.ticket_queue, self.mat.stashed_tickets)

    def update(self, dt):
        """Update game state."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Detect click (mouse down this frame, wasn't down last frame)
        mouse_clicked = mouse_pressed and not self.mouse_was_pressed
        # Detect release (was pressed last frame, not pressed now)
        mouse_released = not mouse_pressed and self.mouse_was_pressed

        # Pee minigame takes over entirely
        if self.pee_minigame_active:
            result = self.pee_minigame.update(pygame.key.get_pressed(), dt)
            if result is not None:
                accuracy = result["accuracy"]
                xp_reward = int(accuracy * PEE_CONFIG["xp_per_accuracy_point"])
                self.player.current_bladder = 0
                if xp_reward > 0:
                    if self.player.gain_xp(xp_reward):
                        self.messages.add_message(f"LEVEL UP! Lv.{self.player.player_level}", (255, 255, 100))
                    self.messages.add_message(f"Relief! {accuracy:.0f}% accuracy (+{xp_reward} XP)", (100, 255, 200))
                else:
                    self.messages.add_message("Relief!", (100, 255, 200))
                self.pee_minigame_active = False
                self.player.save_game()
            self.mouse_was_pressed = mouse_pressed
            return

        # === MAT ANIMATIONS (always run) ===
        self.mat.update(dt)

        # === SIDE MENU SYSTEM (non-blocking) ===

        # 1. Animate panels every frame
        self.side_menus.animate_all(dt)

        # 2. Check trigger clicks (toggle / swap panels)
        triggered = self.side_menus.update_triggers(mouse_pos, mouse_clicked)
        if triggered:
            self._setup_side_panel(triggered)

        # 3. Check close button on active panel
        self.side_menus.update_close_button(mouse_pos, mouse_clicked)

        # 4. Update the active panel's content and handle result
        panel_result = self._update_active_panel(mouse_pos, mouse_clicked)
        if panel_result:
            self._handle_panel_result(panel_result)

        # 5. Gate main game mouse input — don't scratch / click through menus
        mouse_in_menu = self.side_menus.is_point_in_menus(mouse_pos)

        if not mouse_in_menu:
            # --- DRAG SYSTEM ---
            if mouse_clicked and not self.mat.is_dragging:
                self.mat.start_drag(mouse_pos)

            if mouse_pressed and self.mat.is_dragging:
                self.mat.update_drag(mouse_pos)

            if mouse_released and self.mat.is_dragging:
                # Get the side panel rect for stash detection
                side_panel_rect = None
                if self.side_menus.active_panel_key == "ticket_inventory":
                    panel = self.side_menus.panels["ticket_inventory"]
                    if panel.is_open:
                        side_panel_rect = panel.get_panel_rect()

                drag_result = self.mat.end_drag(mouse_pos, side_panel_rect)
                if drag_result:
                    if drag_result["action"] == "redeem":
                        self._redeem_ticket(drag_result["ticket"])
                    elif drag_result["action"] == "stash":
                        self._stash_ticket(drag_result["ticket"])

            # --- SCRATCHING (only when NOT dragging) ---
            if mouse_pressed and not self.mat.is_dragging:
                self.handle_scratch(mouse_pos)

            # PEE action button
            if mouse_clicked:
                if self.main_buttons.pee_btn.enabled:
                    if self.main_buttons.pee_btn.update(mouse_pos, mouse_clicked):
                        self.pee_minigame.start(self.player)
                        self.pee_minigame_active = True

        # Auto mechanics (always run)
        self.auto_scratch(dt)
        self.auto_collect(dt)
        self.player.decay_active_effects(dt)
        self.player.drain_hunger(dt)
        self.player.passive_morale_drain(dt)
        self.player.fill_bladder(dt)

        # Show PEE button when bladder is full
        bladder_full = self.player.current_bladder >= self.player.max_bladder
        self.main_buttons.set_pee_enabled(bladder_full)

        # Pee accident timer — if bladder stays full for 5s, trigger accident
        if bladder_full and not self.pee_minigame_active and not self.pee_accident_active:
            self.pee_accident_timer += dt
            if self.pee_accident_timer >= 5.0:
                self.pee_accident_active = True
                self.pee_cam.start()
                self.pee_accident_timer = 0.0
        elif not bladder_full:
            self.pee_accident_timer = 0.0

        # Update pee accident animation
        if self.pee_accident_active:
            anim_done = self.pee_cam.update(dt)
            if anim_done:
                # Animation finished — set game over, drain bladder
                self.game_lost = True
                self.player.current_bladder = 0
                self.pee_accident_active = False
                self.pee_cam.stop()
                self.messages.add_message("You peed yourself!", (255, 80, 80))

        self.check_for_lose_condition()
        # Drive drunk visuals from active effects
        drunk_active = self.player.active_effects.get("drunk", 0) > 0

        if drunk_active and not self.drunk.enabled:
            self.drunk.enabled = True  # start effect (keep time running)
        elif (not drunk_active) and self.drunk.enabled:
            self.drunk.enabled = False  # stop effect
            self.drunk.time = 0.0  # optional: reset sway phase
            if hasattr(self.drunk, "ghost_trails"):
                self.drunk.ghost_trails.clear()  # optional: clear smear history
            if hasattr(self.drunk, "ghost_positions"):
                self.drunk.ghost_positions.clear()  # optional: clear old ghost positions
            if hasattr(self.drunk, "ghost_cache"):
                self.drunk.ghost_cache.clear()  # optional: rebuild caches next time

        # Stop cigarette if smoking effect expired
        if not self.player.has_effect("smoking"):
            self.cigarette.stop_smoking()

        # Update effects
        self.particles.update(dt)
        self.screen_shake.update(dt)
        self.messages.update(dt)
        # if drunk on update drunk
        self.drunk.update(dt)

        self.mouse_was_pressed = mouse_pressed

    def draw(self):
        """Draw the game."""
        # Pee minigame takes over the screen
        if self.pee_minigame_active:
            self.pee_minigame.draw(self.screen)
            pygame.display.flip()
            return

        shake_offset = self.screen_shake.get_offset()
        drunk_offset = self.drunk.get_offset()

        self.screen.blit(self.background, (0, 0))

        # Draw ticket mat (mat background + tickets + redeem box)
        self.mat.draw(self.screen, shake_offset, drunk_offset, self.drunk)

        # Draw HUD
        self.hud.draw(self.screen, self.player)
        # Draw Morale Bar
        self.morale_bar.draw(self.screen)

        # Draw Hunger Bar
        self.hunger_bar.draw(self.screen)
        # Draw XP Bar
        self.xp_bar.draw(self.screen)
        lvl_text = self.level_font.render(f"LVL {self.player.player_level}", True, (220, 200, 120))
        self.screen.blit(lvl_text, (255, 115))
        # Draw Pee Bar
        self.pee_bar.draw(self.screen)
        # Draw PEE button only (COLLECT phased out)
        if self.main_buttons.pee_btn.enabled:
            self.main_buttons.pee_btn.draw(self.screen)

        # Draw particles
        self.particles.draw(self.screen)

        # Draw messages
        self.messages.draw(self.screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        if self.player.has_effect("smoking"):
            remaining = self.player.active_effects.get("smoking", 0)
            self.cigarette.draw(self.screen, remaining=remaining, total=45)

        # Draw pee accident cam
        if self.pee_accident_active or self.pee_cam.finished:
            self.pee_cam.draw(self.screen)

        # Draw side menus (triggers + panels, on top of game)
        self.side_menus.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            #Control Handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEWHEEL:
                    # Side menu scroll
                    self.side_menus.handle_scroll(event.y, pygame.mouse.get_pos())

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    # Handle drag release via event (backup — also handled in update)
                    if self.mat.is_dragging:
                        side_panel_rect = None
                        if self.side_menus.active_panel_key == "ticket_inventory":
                            panel = self.side_menus.panels["ticket_inventory"]
                            if panel.is_open:
                                side_panel_rect = panel.get_panel_rect()

                        drag_result = self.mat.end_drag(pygame.mouse.get_pos(), side_panel_rect)
                        if drag_result:
                            if drag_result["action"] == "redeem":
                                self._redeem_ticket(drag_result["ticket"])
                            elif drag_result["action"] == "stash":
                                self._stash_ticket(drag_result["ticket"])

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Cancel drag first
                        if self.mat.is_dragging:
                            self.mat.cancel_drag()
                        # Cancel pee minigame
                        elif self.pee_minigame_active:
                            self.pee_minigame.cancel()
                            self.pee_minigame_active = False
                        # Close side menu panel
                        elif self.side_menus.active_panel_key:
                            self.side_menus.close_active()
                        else:
                            self.running = False
                    elif event.key == pygame.K_r:
                        # Reset game (debug)
                        self.player.reset_game()
                        self.mat = TicketMatManager()
                        self.auto_collect_timer = 0
                        self.ticket_shop.setup_buttons(TICKET_TYPES, self.player.get_unlocked_tickets())
                        self.upgrade_shop.setup_buttons(UPGRADES, self.player)
                        self.messages.add_message("Game Reset!", (255, 100, 100))

                    elif event.key == pygame.K_d:
                        # Press D to test things :)
                        self.player.current_hunger -= 10

                keys = pygame.key.get_pressed()

                if self.player.has_effect("smoking") and keys[pygame.K_SPACE]:
                    self.cigarette.start_smoking()
                    if self.player.morale < self.player.morale_cap:
                        self.player.morale += 15 * dt  # morale gain while smoking
                    # XP from smoking
                    if self.player.gain_xp(LEVEL_CONFIG["xp_sources"]["smoking_per_second"] * dt):
                        self.messages.add_message(f"LEVEL UP! Lv.{self.player.player_level}", (255, 255, 100))
                    # Drain cigarette faster while actively puffing
                    self.player.active_effects["smoking"] -= dt * 1.5
                else:
                    self.cigarette.stop_smoking()

            self.update(dt)
            self.draw()

        self.player.save_game()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
