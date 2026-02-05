import json
import os

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
ITEMS = {"beer5":{"name":"Beer",
                 'description':"Get drunk. Increase morale",
                 "base_cost":10,
                 "unlock_level":1},
         "beer4": {"name": "Beer",
                  'description': "Get drunk. Increase morale",
                  "base_cost": 10,
                  "unlock_level": 1},
"beer3":{"name":"Beer",
                 'description':"Get drunk. Increase morale",
                 "base_cost":10,
                 "unlock_level":1},
"beer2":{"name":"Beer",
                 'description':"Get drunk. Increase morale",
                 "base_cost":10,
                 "unlock_level":1},
"beer1":{"name":"Beer",
                 'description':"Get drunk. Increase morale",
                 "base_cost":10,
                 "unlock_level":1},
"beer6":{"name":"Beer",
                 'description':"Get drunk. Increase morale",
                 "base_cost":10,
                 "unlock_level":1}
         }

class Inventory:
    def __init__(self):
        self.all_game_items = ITEMS
        self.items_in_inventory = {} #item:amount
        self.setup_inventory()
    def add_to_inventory(self,item,amount):
        """Looks up item by key and adds that amount"""
        self.items_in_inventory[item] += amount
    def setup_inventory(self):
        """Loops through every item and sets item amounts to 0 """
        for key, config in self.all_game_items.items():
            self.items_in_inventory[config['name'].lower()] = 0


class Player:
    def __init__(self):
        self.money = 5.0  # Start with $5
        self.total_earned = 0.0  # Track lifetime earnings for unlocks
        self.total_spent = 0.0
        self.tickets_scratched = 0
        self.biggest_win = 0
        self.morale = 100
        self.morale_cap = 100
        self.player_level = 1
        self.inventory = Inventory()
        for key, amount in self.inventory.items_in_inventory.items():
            print(key)

        # Upgrade levels
        self.upgrades = {key: 0 for key in UPGRADES}
        # Item unlock levels
        self.item_unlock_requirements = {key: data["unlock_level"] for key, data in ITEMS.items()}


        # Try to load saved game
        self.save_file = "savegame.json"
        self.load_game()

    def get_luck_bonus(self):
        """Get the luck bonus from upgrades."""
        return self.upgrades["lucky_charm"]

    def get_scratch_radius(self):
        """Get scratch radius based on upgrade level."""
        base_radius = 20
        bonus = self.upgrades["scratch_speed"] * 5
        return base_radius + bonus

    def get_auto_scratch_speed(self):
        """Get auto-scratch speed (scratches per second)."""
        level = self.upgrades["auto_scratcher"]
        if level == 0:
            return 0
        return level * 2  # 2, 4, 6, 8, 10 scratches per second

    def get_bulk_amount(self):
        """Get how many tickets can be bought at once."""
        return 1 + self.upgrades["bulk_buy"]

    def get_auto_collect_delay(self):
        """Get auto-collect delay in seconds. Returns None if not unlocked."""
        level = self.upgrades["auto_collect"]
        if level == 0:
            return None
        # Level 1 = 3s, Level 2 = 2.5s, Level 3 = 2s, Level 4 = 1.5s, Level 5 = 1s
        return 3.5 - (level * 0.5)

    def get_upgrade_cost(self, upgrade_key):
        """Calculate the cost for the next level of an upgrade."""
        upgrade = UPGRADES[upgrade_key]
        level = self.upgrades[upgrade_key]
        if level >= upgrade["max_level"]:
            return None  # Maxed out
        return int(upgrade["base_cost"] * (upgrade["cost_multiplier"] ** level))
    def get_item_cost(self,item_key):
        item = ITEMS[item_key]
        item_level = self.item_unlock_requirements[item_key]
        if item_level > self.player_level: # level not high enough
            return None
        return int(item["base_cost"])

    def can_afford_upgrade(self, upgrade_key):
        """Check if player can afford an upgrade."""
        cost = self.get_upgrade_cost(upgrade_key)
        if cost is None:
            return False
        return self.money >= cost

    def buy_upgrade(self, upgrade_key):
        """Purchase an upgrade. Returns True if successful."""
        cost = self.get_upgrade_cost(upgrade_key)
        if cost is None:
            return False
        if self.money >= cost:
            self.money -= cost
            self.total_spent += cost
            self.upgrades[upgrade_key] += 1
            self.save_game()
            return True
        return False
    def buy_item(self, item_key):
        cost = self.get_item_cost(item_key)
        if cost is None:
            return False
        if self.money >= cost:
            self.money -= cost
            self.total_spent+= cost
            self.inventory.add_to_inventory(item_key,1)
            self.save_game()
            return True
        return False
    def can_afford(self, amount):
        """Check if player can afford something."""
        return self.money >= amount

    def spend(self, amount):
        """Spend money. Returns True if successful."""
        if self.money >= amount:
            self.money -= amount
            self.total_spent += amount
            return True
        return False

    def earn(self, amount):
        """Earn money."""
        self.money += amount
        self.total_earned += amount
        if amount > self.biggest_win:
            self.biggest_win = amount
    def lose_morale(self, amount):
        print(self.morale)
        if self.morale > 0:
            if self.morale - amount <= 0:
                return
            else:
                self.morale -= amount
    def gain_morale(self,amount):
        print(self.morale)
        if self.morale + amount > self.morale_cap:
            self.morale = self.morale_cap
        else:
            self.morale += amount
    def scratch_ticket(self):
        """Record a scratched ticket."""
        self.tickets_scratched += 1

    def get_unlocked_tickets(self):
        """Get list of ticket types the player has unlocked."""
        from game.ticket import TICKET_TYPES
        unlocked = []
        for key, config in TICKET_TYPES.items():
            if self.total_earned >= config["unlock_threshold"]:
                unlocked.append(key)
        return unlocked

    def save_game(self):
        """Save game state to file."""
        data = {
            "money": self.money,
            "total_earned": self.total_earned,
            "total_spent": self.total_spent,
            "tickets_scratched": self.tickets_scratched,
            "biggest_win": self.biggest_win,
            "upgrades": self.upgrades,
            "items":self.inventory.items_in_inventory
        }
        try:
            with open(self.save_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Could not save game: {e}")

    def load_game(self):
        """Load game state from file."""
        if not os.path.exists(self.save_file):
            return

        try:
            with open(self.save_file, "r") as f:
                data = json.load(f)

            self.money = data.get("money", 5.0)
            self.total_earned = data.get("total_earned", 0.0)
            self.total_spent = data.get("total_spent", 0.0)
            self.tickets_scratched = data.get("tickets_scratched", 0)
            self.biggest_win = data.get("biggest_win", 0)

            # Load upgrades (handle missing keys)
            saved_upgrades = data.get("upgrades", {})
            for key in UPGRADES:
                self.upgrades[key] = saved_upgrades.get(key, 0)
            # Load Items (handle missing keys)
            saved_items  = data.get("items",{})
            for key in ITEMS:
                self.inventory.items_in_inventory[key] = saved_items.get(key,0)

        except Exception as e:
            print(f"Could not load game: {e}")

    def reset_game(self):
        """Reset all progress."""
        self.money = 5.0
        self.total_earned = 0.0
        self.total_spent = 0.0
        self.tickets_scratched = 0
        self.biggest_win = 0
        self.upgrades = {key: 0 for key in UPGRADES}
        self.save_game()
