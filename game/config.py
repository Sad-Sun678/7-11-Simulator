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

SYMBOL_IMAGES = {
    "cherry": pygame.image.load("assets/symbols/cherry.png"),
    "lemon": pygame.image.load("assets/symbols/lemon.png"),
    "grape": pygame.image.load("assets/symbols/grape.png"),
    "bell": pygame.image.load("assets/symbols/bell.png"),
    "seven": pygame.image.load("assets/symbols/seven.png"),
    "diamond": pygame.image.load("assets/symbols/diamond.png"),
    "star": pygame.image.load("assets/symbols/star.png"),
    "orange": pygame.image.load("assets/symbols/orange.png")
}

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
        "color": (200, 100, 150),  # Pink
        "scratch_color": (220, 180, 200),
        "symbols": ["cherry", "lemon", "orange", "grape", "bell"],  # Available symbols
        "unlock_threshold": 25,
        "ticket_class": "match3",
    },
    "lucky7": {
        "name": "Lucky 7s",
        "cost": 5,
        "color": (180, 100, 180),  # Purple
        "scratch_color": (200, 180, 200),
        "prizes": [0, 0, 0, 0, 7, 7, 14, 21, 49, 77],
        "unlock_threshold": 50,
        "ticket_class": "standard",
    },
    "match3_deluxe": {
        "name": "Match 3 Deluxe",
        "cost": 8,
        "color": (100, 180, 200),  # Teal
        "scratch_color": (180, 210, 220),
        "symbols": ["orange", "grape", "bell", "seven", "diamond"],  # Better symbols
        "unlock_threshold": 150,
        "ticket_class": "match3",
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
    }
}
