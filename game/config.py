








import pygame

# Symbol definitions for Match 3 tickets
SYMBOLS = {
    "cherry": {"color": (220, 50, 50), "value": 5, "shape": "circle"},
    "lemon": {"color": (255, 220, 50), "value": 10, "shape": "oval"},
    "orange": {"color": (255, 150, 50), "value": 15, "shape": "circle"},
    "grape": {"color": (150, 50, 200), "value": 25, "shape": "cluster"},
    "bell": {"color": (255, 215, 0), "value": 50, "shape": "bell"},
    "seven": {"color": (255, 50, 50), "value": 77, "shape": "seven"},
    "diamond": {"color": (100, 200, 255), "value": 100, "shape": "diamond"},
    "star": {"color": (255, 255, 100), "value": 200, "shape": "star"},
}

SYMBOL_IMAGES = {}

def load_symbol_images():
    if SYMBOL_IMAGES:
        return
    SYMBOL_IMAGES.update({
        "cherry": pygame.image.load("assets/symbols/cherry.png"),
        "lemon": pygame.image.load("assets/symbols/lemon.png"),
        "grape": pygame.image.load("assets/symbols/grape.png"),
        "bell": pygame.image.load("assets/symbols/bell.png"),
        "seven": pygame.image.load("assets/symbols/seven.png"),
        "diamond": pygame.image.load("assets/symbols/diamond.png"),
        "star": pygame.image.load("assets/symbols/star.png"),
        "orange": pygame.image.load("assets/symbols/orange.png"),
    })

# Custom ticket artwork — loaded once, keyed by filename
# Each ticket type can specify any of these image keys in its config:
#   "scratch_image"  — full-ticket scratch cover PNG (replaces solid color fill)
#   "base_image"     — full-ticket background PNG (replaces procedural chrome)
#   "cell_icon_image" — small PNG drawn centered in each scratch cell (replaces "?" text)
#   "cell_cover_image"— PNG used as the scratch cell box itself (replaces the drawn rect)
# PNGs go in assets/tickets/ and are scaled at draw time.
TICKET_IMAGES = {}

_TICKET_IMAGE_KEYS = ("scratch_image", "base_image", "cell_icon_image", "cell_cover_image")

def load_ticket_images():
    """Load all unique ticket artwork PNGs referenced by TICKET_TYPES.
    Call once after pygame.display is initialised (same time as load_symbol_images)."""
    import os
    if TICKET_IMAGES:
        return
    # Gather every unique filename referenced by any ticket type
    needed = set()
    for cfg in TICKET_TYPES.values():
        for key in _TICKET_IMAGE_KEYS:
            fname = cfg.get(key)
            if fname:
                needed.add(fname)
    for fname in needed:
        path = os.path.join("assets", "tickets", fname)
        if os.path.isfile(path):
            TICKET_IMAGES[fname] = pygame.image.load(path).convert_alpha()
        else:
            print(f"[ticket art] WARNING: {path} not found — will use fallback")

# Ticket type definitions
TICKET_TYPES = {
    "chud":{"name":"loser",
            "cost":0,
            "color":(204,0,0),  #Red
            "scratch_color":(180,180,180), #Gray
            "prizes":[0,0,0,0,0,0,0,0,0,0],
            "unlock_threshold":0,
            "ticket_class": "standard",
            },
    "winner":{"name":"winner",
            "cost":0,
            "color":(0,255,0),  #Red
            "scratch_color":(180,180,180), #Gray
            "prizes":[1000],
            "unlock_threshold":0,
            "ticket_class": "standard",
            },
    "basic": {
        "name": "Basic",
        "cost": 1,
        "color": (100, 180, 100),  # Green
        "scratch_color": (180, 180, 180),  # Gray
        "prizes": [0, 0, 0, 0, 0, 1, 1, 2, 5, 10],  # Weighted prizes
        "unlock_threshold": 0,
        "ticket_class": "standard",
    },
    "match3": {
        "name": "Match 3",
        "cost": 3,
        "color": (255,0,0),  # Red
        "scratch_color": (220, 180, 200),
        "scratch_image":"test_surface.png",
        "symbols": ["cherry", "lemon", "orange", "grape", "bell"],  # Available symbols
        "unlock_threshold": 25,
        "ticket_class": "match3",
        "layout": {
            "ticket_width": 340,
            "ticket_height": 400,
            "cell_size": 40,  # bigger cells
            "grid_x": 100,  # pin grid 30px from left
            "grid_y": 225,  # pin grid 120px from top
        },
    },
    "lady_luck": {
        "name": "Lady Luck",
        "cost": 5,
        "color": (180, 100, 180),  # Purple
        "scratch_color": (200, 180, 200),
        "prizes": [0, 0, 0, 0, 7, 7, 14, 21, 49, 77],
        "unlock_threshold": 50,
        "ticket_class": "standard",
    },
    "gold_rush": {
        "name": "Gold Rush",
        "cost": 8,
        "color": (100, 180, 200),  # Teal
        "scratch_color": (180, 210, 220),
        "scratch_image":"gold_rush.png",
        "base_image":"gold_rush_bg.png",
        "cell_cover_image": "gold_rush_cover.png",  # custom tile box
        "cell_icon_image": "gold_rush_symbol.png",  # replaces the "?"
        "symbols": ["orange", "grape", "bell", "seven", "diamond"],  # Better symbols
        "unlock_threshold": 150,
        "ticket_class": "match3",
        "layout": {
            "ticket_width": 600,
            "ticket_height": 300,
            "cell_size": 64,  # bigger cells
            "grid_x": 350,  # pin grid 30px from left
            "grid_y": 40,  # pin grid 120px from top
        },

    },
    "bigmoney": {
        "name": "Big Money",
        "cost": 10,
        "color": (100, 150, 200),  # Blue
        "scratch_color": (180, 200, 220),
        "prizes": [0, 0, 0, 0, 0, 10, 25, 50, 100, 500],
        "unlock_threshold": 200,
        "ticket_class": "standard",
    },
    "match3_mega": {
        "name": "Mega Match",
        "cost": 15,
        "color": (220, 180, 100),  # Orange-gold
        "scratch_color": (240, 210, 180),
        "symbols": ["bell", "seven", "diamond", "star"],  # Premium symbols only
        "unlock_threshold": 500,
        "ticket_class": "match3",
    },
    "jackpot": {
        "name": "Jackpot",
        "cost": 25,
        "color": (220, 180, 80),  # Gold
        "scratch_color": (240, 220, 180),
        "prizes": [0, 0, 0, 0, 0, 0, 50, 100, 500, 5000],
        "unlock_threshold": 1000,
        "ticket_class": "standard",
    },
    "lucky_sevens": {
        "name": "Lucky Sevens",
        "cost": 12,
        "color": (80, 140, 200),
        "scratch_color": (190, 200, 220),
        "scratch_image": "lucky_seven.png",
        "base_image": "lucky_seven_bg.png",
        "cell_cover_image": "lucky_seven_cover.png",
        "cell_icon_image": "lucky_seven_symbol.png",
        "cell_prizes": [1, 2, 5, 5, 10, 10, 15, 20, 25, 50],
        "multipliers": [1, 1, 1, 1, 1, 2, 2, 3, 5],
        "unlock_threshold": 300,
        "ticket_class": "number_match",
        "layout": {
            "ticket_width": 350,
            "ticket_height": 500,
            "win_row_x": 40,
            "win_row_y": 150,
            "win_cell_w": 50,
            "win_cell_h": 40,
            "grid_x": 70,
            "grid_y": 165,
            "cell_w": 40,
            "cell_h": 40,
            "multiplier_x": 260,
            "multiplier_y": 375,
            "multiplier_w": 60,
            "multiplier_h": 45,
        },
    },
    "number_match_gold": {
        "name": "Gold Rush",
        "cost": 30,
        "color": (200, 160, 60),  # Rich gold
        "scratch_color": (230, 215, 170),
        "cell_prizes": [5, 10, 20, 25, 50, 50, 100, 100, 250, 500],
        "multipliers": [1, 1, 1, 2, 2, 3, 3, 5, 10],
        "unlock_threshold": 1500,
        "ticket_class": "number_match",
    },
}

# Upgrade definitions
UPGRADES = {
    "lucky_charm": {
        "name": "Lucky Charm",
        "description": "Increases win chance",
        "base_cost": 25,
        "cost_multiplier": 1.8,
        "max_level": 10,
        "icon": "",
    },
    "scratch_speed": {
        "name": "Scratch Speed",
        "description": "Larger scratch radius",
        "base_cost": 15,
        "cost_multiplier": 1.5,
        "max_level": 10,
        "icon": "",
    },
    "auto_scratcher": {
        "name": "Auto Scratcher",
        "description": "Slowly scratches tickets",
        "base_cost": 100,
        "cost_multiplier": 2.5,
        "max_level": 5,
        "icon": "",
    },
    "auto_collect": {
        "name": "Auto Collect",
        "description": "Auto-redeem completed tickets",
        "base_cost": 75,
        "cost_multiplier": 2.0,
        "max_level": 5,
        "icon": "",
    },
    "bulk_buy": {
        "name": "Bulk Buy",
        "description": "Buy multiple tickets",
        "base_cost": 50,
        "cost_multiplier": 2.0,
        "max_level": 5,
        "icon": "",
    },
    "lucky_charm1": {
        "name": "Lucky Charm",
        "description": "Increases win chance",
        "base_cost": 25,
        "cost_multiplier": 1.8,
        "max_level": 10,
        "icon": "",
    },
    "lucky_charm2": {
        "name": "Lucky Charm",
        "description": "Increases win chance",
        "base_cost": 25,
        "cost_multiplier": 1.8,
        "max_level": 10,
        "icon": "",
    },
    "lucky_charm3": {
        "name": "Lucky Charm",
        "description": "Increases win chance",
        "base_cost": 25,
        "cost_multiplier": 1.8,
        "max_level": 10,
        "icon": "",
    },
}

ITEMS = {
    "beer": {
        "name": "Beer",
        "description": "Get drunk. Increase morale",
        "base_cost": 10,
        "unlock_level": 1,
        "effects": ["drunk", "lucky"],
    },
    "cigarette": {
        "name": "Cigarette",
        "description": "Light up a smoke. Hold SPACE to puff.",
        "base_cost": 5,
        "unlock_level": 1,
        "effects": ["smoking"],
    }
}

# Level / XP configuration
LEVEL_CONFIG = {
    "xp_base": 100,            # XP needed for level 2
    "xp_growth": 1.6,          # Each level requires 1.6x more XP than the last
    "max_level": 50,
    "xp_sources": {
        "smoking_per_second": 2,    # XP/sec while holding SPACE
        "scratch_per_cell": 2,      # XP per new area scratched
        "ticket_complete": 25,      # XP for completing any ticket
        "winner_bonus": 50,         # Extra XP for winning tickets
    },
    "rewards_per_level": {
        "luck_bonus": 0.5,          # +0.5 luck per level
        "morale_cap_bonus": 2,      # +2 morale cap per level
        "scratch_radius_bonus": 0.3 # +0.3 scratch radius per level
    }
}

# Pee minigame configuration
PEE_CONFIG = {
    "max_bladder": 100,
    "bladder_fill_rate": 0,       # per second (full in ~50s)
    "pee_drain_rate": 15.0,         # bladder drain per second WHILE hitting bowl
    "stream_radius": 8,             # visual pee stream radius
    "bowl_x": 920,                  # bowl center X (adjust to match your toilet_bg)
    "bowl_y": 520,                  # bowl center Y (adjust to match your toilet_bg)
    "bowl_radius": 80,              # circular hitbox radius
    "xp_per_accuracy_point": 1.0,   # XP = accuracy% * this (100% accuracy = 100 XP)
}
