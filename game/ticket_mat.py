"""Multi-ticket mat system with deal animations, drag-and-drop, and redeem box."""

import pygame
import random
import math
from game.animations import Tween, TweenGroup, AnimationManager


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------
MAX_TICKETS_ON_MAT = 4
MAT_X = 350
MAT_Y = 120
MAT_W = 1100
MAT_H = 620
DEAL_DURATION = 0.35        # seconds for deal-in slide
STASH_DURATION = 0.4        # seconds for shrink+fly
DISSOLVE_DURATION = 0.6     # seconds for loser fade-out
SNAP_DURATION = 0.2         # seconds for snap-back animation
MAT_PADDING = 10            # inset from mat edge when clamping tickets


# ---------------------------------------------------------------------------
# RedeemBox — drop zone below the mat
# ---------------------------------------------------------------------------
class RedeemBox:
    """Visual drop zone. Drag a completed ticket here to collect its prize."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)

    def contains_point(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, screen, is_hovering=False):
        # Background
        if is_hovering:
            bg_color = (40, 120, 40, 140)
            border_color = (80, 220, 80)
            text_color = (180, 255, 180)
        else:
            bg_color = (50, 55, 65, 100)
            border_color = (100, 100, 120)
            text_color = (160, 160, 170)

        # Semi-transparent fill
        surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        surf.fill(bg_color)
        screen.blit(surf, self.rect.topleft)

        # Dashed border
        self._draw_dashed_rect(screen, border_color, self.rect, dash_len=10, gap=6, width=2)

        # Label
        label = "DROP TO REDEEM" if not is_hovering else "RELEASE TO COLLECT!"
        text_surf = self.font.render(label, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    @staticmethod
    def _draw_dashed_rect(screen, color, rect, dash_len=10, gap=6, width=2):
        """Draw a rectangle with dashed edges."""
        x, y, w, h = rect
        # Top
        RedeemBox._draw_dashed_line(screen, color, (x, y), (x + w, y), dash_len, gap, width)
        # Bottom
        RedeemBox._draw_dashed_line(screen, color, (x, y + h), (x + w, y + h), dash_len, gap, width)
        # Left
        RedeemBox._draw_dashed_line(screen, color, (x, y), (x, y + h), dash_len, gap, width)
        # Right
        RedeemBox._draw_dashed_line(screen, color, (x + w, y), (x + w, y + h), dash_len, gap, width)

    @staticmethod
    def _draw_dashed_line(screen, color, start, end, dash_len, gap, width):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = max(1, math.hypot(dx, dy))
        dx /= length
        dy /= length
        pos = 0
        drawing = True
        while pos < length:
            seg = dash_len if drawing else gap
            seg = min(seg, length - pos)
            if drawing:
                sx = start[0] + dx * pos
                sy = start[1] + dy * pos
                ex = start[0] + dx * (pos + seg)
                ey = start[1] + dy * (pos + seg)
                pygame.draw.line(screen, color, (int(sx), int(sy)), (int(ex), int(ey)), width)
            pos += seg
            drawing = not drawing


# ---------------------------------------------------------------------------
# TicketMatManager
# ---------------------------------------------------------------------------
class TicketMatManager:
    """Manages multi-ticket mat: dealing, dragging, redeeming, stashing.

    Tickets are freely positioned anywhere on the mat (no fixed slots).
    The list order = draw order: last element is drawn on top.
    Touching / dragging a ticket promotes it to the top of the draw list.
    Only the topmost ticket at a given point can be scratched — no
    stacking exploits.
    """

    def __init__(self):
        self.mat_rect = pygame.Rect(MAT_X, MAT_Y, MAT_W, MAT_H)

        # Ticket lists  (mat_tickets order == z-order, last = top)
        self.mat_tickets = []           # on the mat (max MAX_TICKETS_ON_MAT)
        self.ticket_queue = []          # waiting to be dealt
        self.stashed_tickets = []       # stored in ticket inventory

        # Animation
        self.animations = AnimationManager()
        self._dealing_set = set()       # tickets currently sliding in
        self._dissolving = {}           # ticket id -> alpha (fading losers)
        self._snapping = set()          # tickets currently snapping back

        # Drag state
        self.dragging_ticket = None
        self._drag_started = False

        # Stash fly targets (updated by main when side menu panel is known)
        self.stash_target_pos = (1700, 400)  # default; overridden at runtime

        # Redeem box — centred below the mat
        redeem_w = 500
        redeem_x = self.mat_rect.centerx - redeem_w // 2
        redeem_y = self.mat_rect.bottom + 15
        self.redeem_box = RedeemBox(redeem_x, redeem_y, redeem_w, 60)

        # Mat surface (static background — drawn once)
        self.mat_surface = self._create_mat_surface()

        # Queue count font
        self.queue_font = pygame.font.Font(None, 24)

    # ------------------------------------------------------------------
    # Mat surface (background)
    # ------------------------------------------------------------------

    def _create_mat_surface(self):
        mat = pygame.Surface((self.mat_rect.width, self.mat_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mat, (45, 50, 60), mat.get_rect(), border_radius=15)
        pygame.draw.rect(mat, (65, 70, 80), mat.get_rect(), 2, border_radius=15)

        font = pygame.font.Font(None, 32)
        hint = font.render("Buy a ticket to start!", True, (80, 85, 95))
        mat.blit(hint, (
            self.mat_rect.width // 2 - hint.get_width() // 2,
            self.mat_rect.height // 2,
        ))
        return mat

    # ------------------------------------------------------------------
    # Free-placement helpers
    # ------------------------------------------------------------------

    def _pick_deal_position(self, ticket):
        """Choose a random landing position inside the mat for a new ticket,
        trying to avoid overlapping existing tickets too much."""
        # Available area (ticket must fit inside mat)
        min_x = self.mat_rect.x + MAT_PADDING
        max_x = self.mat_rect.right - ticket.width - MAT_PADDING
        min_y = self.mat_rect.y + MAT_PADDING
        max_y = self.mat_rect.bottom - ticket.height - MAT_PADDING

        if max_x < min_x:
            max_x = min_x
        if max_y < min_y:
            max_y = min_y

        # Try a few random positions, pick the one with least overlap
        best_pos = (min_x, min_y)
        best_overlap = float("inf")

        for _ in range(12):
            cx = random.randint(int(min_x), int(max_x))
            cy = random.randint(int(min_y), int(max_y))
            candidate = pygame.Rect(cx, cy, ticket.width, ticket.height)
            overlap = 0
            for other in self.mat_tickets:
                if other is ticket:
                    continue
                other_rect = pygame.Rect(other.x, other.y, other.width, other.height)
                inter = candidate.clip(other_rect)
                overlap += inter.width * inter.height
            if overlap < best_overlap:
                best_overlap = overlap
                best_pos = (cx, cy)

        return best_pos

    def _clamp_to_mat(self, ticket):
        """Clamp a ticket's position so it stays within the mat bounds."""
        min_x = self.mat_rect.x + MAT_PADDING
        max_x = self.mat_rect.right - ticket.width - MAT_PADDING
        min_y = self.mat_rect.y + MAT_PADDING
        max_y = self.mat_rect.bottom - ticket.height - MAT_PADDING
        ticket.x = max(min_x, min(ticket.x, max_x))
        ticket.y = max(min_y, min(ticket.y, max_y))

    def _promote_to_top(self, ticket):
        """Move a ticket to the end of mat_tickets so it draws on top."""
        if ticket in self.mat_tickets:
            self.mat_tickets.remove(ticket)
            self.mat_tickets.append(ticket)

    # ------------------------------------------------------------------
    # Add / deal tickets
    # ------------------------------------------------------------------

    def add_ticket(self, ticket):
        """Add a newly purchased ticket. Deals onto mat if room, else queues."""
        if len(self.mat_tickets) < MAX_TICKETS_ON_MAT:
            self._deal_to_mat(ticket)
        else:
            self.ticket_queue.append(ticket)

    def _deal_to_mat(self, ticket):
        """Place ticket on the mat with a slide-in animation to a random spot."""
        self.mat_tickets.append(ticket)

        target_x, target_y = self._pick_deal_position(ticket)
        start_x = self.mat_rect.right + 50  # start off-screen right

        ticket.set_position(start_x, target_y)
        self._dealing_set.add(id(ticket))

        tween_x = Tween(start_x, target_x, DEAL_DURATION, "ease_out_back")
        tween_y = Tween(target_y, target_y, DEAL_DURATION, "linear")
        group = TweenGroup({"x": tween_x, "y": tween_y})

        def on_deal_done():
            ticket.set_position(target_x, target_y)
            self._dealing_set.discard(id(ticket))

        self.animations.add(group, callback=on_deal_done, tag=f"deal_{id(ticket)}")

    def _deal_next(self):
        """Deal the next queued ticket onto the mat if there's room."""
        while self.ticket_queue and len(self.mat_tickets) < MAX_TICKETS_ON_MAT:
            ticket = self.ticket_queue.pop(0)
            self._deal_to_mat(ticket)

    # ------------------------------------------------------------------
    # Remove tickets from mat
    # ------------------------------------------------------------------

    def remove_ticket(self, ticket):
        """Remove a ticket from the mat."""
        if ticket in self.mat_tickets:
            self.mat_tickets.remove(ticket)
        # Deal next from queue
        self._deal_next()

    # ------------------------------------------------------------------
    # Dissolve losers
    # ------------------------------------------------------------------

    def dissolve_ticket(self, ticket):
        """Start a fade-out animation for a $0 loser ticket."""
        self._dissolving[id(ticket)] = 255.0  # start fully opaque

        tw = Tween(255, 0, DISSOLVE_DURATION, "ease_in_quad")

        def on_dissolve_done():
            self._dissolving.pop(id(ticket), None)
            self.remove_ticket(ticket)

        self.animations.add(tw, callback=on_dissolve_done, tag=f"dissolve_{id(ticket)}")

    # ------------------------------------------------------------------
    # Drag system
    # ------------------------------------------------------------------

    def start_drag(self, mouse_pos):
        """Try to start dragging a ticket by its handle. Returns True if drag started.
        Checks topmost ticket first (reversed list = top of z-order)."""
        if self.dragging_ticket is not None:
            return False

        # Check tickets in reverse order (topmost first)
        for ticket in reversed(self.mat_tickets):
            # Skip tickets that are currently animating
            if id(ticket) in self._dealing_set or id(ticket) in self._dissolving:
                continue
            if ticket.get_handle_rect().collidepoint(mouse_pos):
                self.dragging_ticket = ticket
                ticket.dragging = True
                ticket.drag_offset = (mouse_pos[0] - ticket.x, mouse_pos[1] - ticket.y)
                self._drag_started = True
                # Promote to top of draw order
                self._promote_to_top(ticket)
                # Cancel any snap animation for this ticket
                self.animations.cancel(f"reslot_{id(ticket)}")
                self._snapping.discard(id(ticket))
                return True
        return False

    def update_drag(self, mouse_pos):
        """Move the dragging ticket to follow the mouse, clamped to mat."""
        if self.dragging_ticket is None:
            return
        t = self.dragging_ticket
        t.set_position(
            mouse_pos[0] - t.drag_offset[0],
            mouse_pos[1] - t.drag_offset[1]
        )
        # Don't clamp while dragging — allow pulling off-mat to reach redeem box / panel

    def end_drag(self, mouse_pos, side_panel_rect=None):
        """Release the dragging ticket. Returns action dict or None.

        Possible returns:
            {"action": "redeem", "ticket": ticket}
            {"action": "stash", "ticket": ticket}
            None  (clamp back to mat)
        """
        if self.dragging_ticket is None:
            return None

        ticket = self.dragging_ticket
        ticket.dragging = False
        self.dragging_ticket = None
        self._drag_started = False

        # Check redeem box
        if self.redeem_box.contains_point(mouse_pos) and ticket.is_complete():
            return {"action": "redeem", "ticket": ticket}

        # Check stash (over ticket inventory side panel area)
        if side_panel_rect and side_panel_rect.collidepoint(mouse_pos):
            return {"action": "stash", "ticket": ticket}

        # Clamp back into mat bounds (smooth snap)
        clamped_x = max(self.mat_rect.x + MAT_PADDING,
                        min(ticket.x, self.mat_rect.right - ticket.width - MAT_PADDING))
        clamped_y = max(self.mat_rect.y + MAT_PADDING,
                        min(ticket.y, self.mat_rect.bottom - ticket.height - MAT_PADDING))

        if abs(ticket.x - clamped_x) > 2 or abs(ticket.y - clamped_y) > 2:
            # Animate snap to clamped position
            tween_x = Tween(ticket.x, clamped_x, SNAP_DURATION, "ease_out_quad")
            tween_y = Tween(ticket.y, clamped_y, SNAP_DURATION, "ease_out_quad")
            group = TweenGroup({"x": tween_x, "y": tween_y})
            self._snapping.add(id(ticket))

            def on_snap():
                ticket.set_position(clamped_x, clamped_y)
                self._snapping.discard(id(ticket))

            self.animations.add(group, callback=on_snap, tag=f"snap_{id(ticket)}")
        else:
            ticket.set_position(clamped_x, clamped_y)

        return None

    def cancel_drag(self):
        """Cancel an in-progress drag (e.g. on ESC) — snap back into mat."""
        if self.dragging_ticket:
            self.end_drag((0, 0))  # will clamp into mat

    @property
    def is_dragging(self):
        return self.dragging_ticket is not None

    # ------------------------------------------------------------------
    # Stash / unstash
    # ------------------------------------------------------------------

    def stash_ticket(self, ticket):
        """Move a ticket from mat to stashed list."""
        self.stashed_tickets.append(ticket)
        self.remove_ticket(ticket)

    def unstash_ticket(self, ticket, mouse_pos):
        """Pull a stashed ticket back to the mat at the mouse position for dragging."""
        if ticket in self.stashed_tickets:
            self.stashed_tickets.remove(ticket)

        # Place at mouse position and start dragging
        ticket.set_position(mouse_pos[0] - ticket.width // 2,
                            mouse_pos[1] - ticket.handle_height // 2)

        # Add to mat if room, otherwise queue it
        if len(self.mat_tickets) < MAX_TICKETS_ON_MAT:
            self.mat_tickets.append(ticket)
            self.dragging_ticket = ticket
            ticket.dragging = True
            ticket.drag_offset = (ticket.width // 2, ticket.handle_height // 2)
            self._drag_started = True
        else:
            # No room — just add to queue
            self.ticket_queue.append(ticket)

    # ------------------------------------------------------------------
    # Query helpers (z-order aware — topmost only)
    # ------------------------------------------------------------------

    def get_ticket_at_point(self, pos):
        """Return the TOPMOST non-animating ticket whose body (below handle)
        contains *pos*. Only the top ticket is returned — stacked tickets
        underneath are blocked, preventing multi-scratch exploits."""
        for ticket in reversed(self.mat_tickets):
            if id(ticket) in self._dealing_set or id(ticket) in self._dissolving:
                continue
            if ticket is self.dragging_ticket:
                continue
            # Full rect (including handle) — if the point lands on this
            # ticket at all, it blocks anything underneath.
            full_rect = pygame.Rect(ticket.x, ticket.y,
                                    ticket.width, ticket.height)
            if full_rect.collidepoint(pos):
                # Only return if the point is on the body (below handle)
                body_rect = pygame.Rect(ticket.x, ticket.y + ticket.handle_height,
                                        ticket.width, ticket.height - ticket.handle_height)
                if body_rect.collidepoint(pos):
                    return ticket
                # Point is on the handle — still blocks scratching but
                # doesn't return a scratchable ticket
                return None
        return None

    def auto_scratch_target(self):
        """Return first non-complete, non-animating ticket on mat, or None."""
        for ticket in self.mat_tickets:
            if id(ticket) in self._dealing_set or id(ticket) in self._dissolving:
                continue
            if not ticket.is_complete():
                return ticket
        return None

    def get_first_complete_winner(self):
        """Return first completed ticket with prize > 0 on the mat, or None."""
        for ticket in self.mat_tickets:
            if id(ticket) in self._dealing_set or id(ticket) in self._dissolving:
                continue
            if ticket is self.dragging_ticket:
                continue
            if ticket.is_complete() and ticket.get_prize() > 0:
                return ticket
        return None

    def has_any_tickets(self):
        """True if any tickets exist on mat, queue, or stash."""
        return bool(self.mat_tickets or self.ticket_queue or self.stashed_tickets)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        """Advance all animations. Called once per frame."""
        self.animations.update(dt)

        # Update positions of dealing/snapping tickets via their tweens
        for entry_tween, _, tag in self.animations._entries:
            if not hasattr(entry_tween, 'tweens'):
                continue  # skip non-TweenGroup entries (dissolve tweens)
            vals = entry_tween.get_values()
            # Find the ticket this animation belongs to
            if tag and tag.startswith(("deal_", "reslot_", "snap_")):
                tid = int(tag.split("_", 1)[1])
                for ticket in self.mat_tickets:
                    if id(ticket) == tid:
                        ticket.set_position(vals.get("x", ticket.x),
                                            vals.get("y", ticket.y))
                        break

        # Update dissolve alpha
        for entry_tween, _, tag in self.animations._entries:
            if tag and tag.startswith("dissolve_"):
                tid = int(tag.split("_", 1)[1])
                if tid in self._dissolving:
                    self._dissolving[tid] = max(0, entry_tween.get_value())

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen, shake_offset=(0, 0), drunk_offset=(0, 0), drunk_effect=None):
        """Draw the mat, tickets, redeem box, and queue indicator.

        Tickets are drawn in list order (index 0 = bottom, last = top).
        The dragged ticket is always drawn last (above everything).
        """
        final_ox = shake_offset[0] + drunk_offset[0]
        final_oy = shake_offset[1] + drunk_offset[1]

        # Mat background
        mat_x = self.mat_rect.x + final_ox
        mat_y = self.mat_rect.y + final_oy

        if drunk_effect and drunk_effect.enabled:
            drunk_effect.draw_double(screen, self.mat_surface, (mat_x, mat_y), "mat")
        else:
            screen.blit(self.mat_surface, (mat_x, mat_y))

        # Redeem box (no shake on UI elements)
        hovering = False
        if self.dragging_ticket and self.dragging_ticket.is_complete():
            ticket_center = (self.dragging_ticket.x + self.dragging_ticket.width // 2,
                             self.dragging_ticket.y + self.dragging_ticket.height // 2)
            hovering = self.redeem_box.contains_point(ticket_center)
        self.redeem_box.draw(screen, is_hovering=hovering)

        # Draw non-dragging tickets in z-order (index 0 = bottom)
        for ticket in self.mat_tickets:
            if ticket is self.dragging_ticket:
                continue  # draw dragged ticket last

            tid = id(ticket)

            # Dissolving ticket — draw with reduced alpha
            if tid in self._dissolving:
                alpha = int(self._dissolving[tid])
                self._draw_ticket_with_alpha(screen, ticket, alpha, final_ox, final_oy, drunk_effect)
                continue

            # Normal ticket with shake/drunk offset
            tx = ticket.x + final_ox
            ty = ticket.y + final_oy

            if drunk_effect and drunk_effect.enabled:
                ticket_offset = drunk_effect.get_ticket_offset()
                tx = ticket.x + final_ox * 0.8 + ticket_offset[0]
                ty = ticket.y + final_oy * 0.8 + ticket_offset[1]

                # Composite ticket surface
                ticket_surface = pygame.Surface(
                    (ticket.width, ticket.height), pygame.SRCALPHA)
                ticket_surface.blit(ticket.base_surface, (0, 0))
                ticket_surface.blit(ticket.scratch_surface, (0, 0))
                drunk_effect.draw_double(screen, ticket_surface, (tx, ty), f"ticket_{tid}")

                # Border
                pygame.draw.rect(screen, (80, 60, 40),
                                 (tx - 2, ty - 2, ticket.width + 4, ticket.height + 4),
                                 4, border_radius=12)

                # Handle
                handle_surf = pygame.Surface((ticket.width, ticket.handle_height), pygame.SRCALPHA)
                handle_surf.fill((0, 0, 0, 60))
                screen.blit(handle_surf, (tx, ty))
                for i in range(3):
                    ly = ty + 9 + i * 6
                    pygame.draw.line(screen, (180, 180, 180),
                                     (tx + ticket.width // 2 - 20, ly),
                                     (tx + ticket.width // 2 + 20, ly), 1)
            else:
                # Save original pos, set offset pos, draw, restore
                orig_x, orig_y = ticket.x, ticket.y
                ticket.set_position(tx, ty)
                ticket.draw(screen)
                ticket.set_position(orig_x, orig_y)

        # Draw dragging ticket on top (no shake offset — follows mouse)
        if self.dragging_ticket:
            self.dragging_ticket.draw(screen)

        # Queue count badge
        if self.ticket_queue:
            badge_text = f"+{len(self.ticket_queue)} queued"
            badge_surf = self.queue_font.render(badge_text, True, (200, 200, 200))
            badge_x = self.mat_rect.right - badge_surf.get_width() - 15
            badge_y = self.mat_rect.bottom - 25
            screen.blit(badge_surf, (badge_x + final_ox, badge_y + final_oy))

    def _draw_ticket_with_alpha(self, screen, ticket, alpha, ox, oy, drunk_effect):
        """Draw a ticket with overall alpha (for dissolve)."""
        if alpha <= 0:
            return
        tx = ticket.x + ox
        ty = ticket.y + oy

        # Composite into temp surface then apply alpha
        temp = pygame.Surface((ticket.width + 4, ticket.height + 4), pygame.SRCALPHA)
        # Draw ticket onto temp at (2, 2) offset for border
        orig_x, orig_y = ticket.x, ticket.y
        ticket.set_position(2, 2)
        ticket.draw(temp)
        ticket.set_position(orig_x, orig_y)

        # Apply alpha
        temp.set_alpha(alpha)
        screen.blit(temp, (tx - 2, ty - 2))
