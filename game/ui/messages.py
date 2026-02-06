import pygame


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
                rect = text_surface.get_rect(center=(center_x + 50, center_y + 120 + y_offset))
                screen.blit(text_surface, rect)
                y_offset -= 50
            elif msg['flag'] == "WIN_PRIZE":
                text_surface = self.font.render(msg["text"], True, msg["color"])
                text_surface.set_alpha(msg["alpha"])
                rect = text_surface.get_rect(center=(center_x+50, center_y + 150 + y_offset))
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
