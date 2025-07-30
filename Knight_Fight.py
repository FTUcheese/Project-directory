import copy
import random
import asyncio

# ---- Required for OpenAI in PyScript ----
try:
    import pyodide_http
    pyodide_http.patch_all()
except ImportError:
    pass

def write_to(element_id, html, append=False):
    from js import document
    el = document.getElementById(element_id)
    if el is not None:
        if append:
            el.innerHTML = el.innerHTML + html
        else:
            el.innerHTML = html

battle = None  # GLOBAL battle variable for all functions
manual_swap_pending = None  # (player_num, slot_idx) or None
BOT_ACTIVE = False

# == Game Data (minimal demo version, add more as needed) ==
class Move:
    def __init__(self, name, faction, power, accuracy=100, description=""):
        self.name = name
        self.faction = faction
        self.power = power
        self.accuracy = accuracy
        self.description = description

class Ability:
    def __init__(self, name, faction, description):
        self.name = name
        self.faction = faction
        self.description = description

class KnightTemplate:
    def __init__(self, name, faction, hp, attack, defense, speed, learnset):
        self.name = name
        self.faction = faction
        self.base_stats = {'hp': hp, 'atk': attack, 'def': defense, 'spd': speed}
        self.learnset = learnset

ALL_ABILITIES = {
    "Divine Power": Ability("Divine Power", "Radiant", "In Blazing Sun, Attack is boosted."),
    "Bodyguard": Ability("Bodyguard", "Steel", "Redirects attacks from ally to this Knight."),
    "Frozenheart": Ability("Frozenheart", "Cryo", "Heals in Hailstorm."),
    "Last Stand": Ability("Last Stand", "Radiant", "1.5x damage when HP is low."),
}
ALL_MOVES = {
    "Empowered Strike": Move("Empowered Strike", "Generic", 60, 85, "A powerful but less accurate blow."),
    "Guard Bash": Move("Guard Bash", "Steel", 55, 90, "A headbutt that may daze."),
    "Blazing Judgment": Move("Blazing Judgment", "Radiant", 80, 90, "Absorbs light, then fires."),
    "Sunfire Burst": Move("Sunfire Burst", "Radiant", 70, 100, "Blast of fire."),
    "Consecration": Move("Consecration", "Radiant", 0, 100, "Special."),
    "Sacred Blade": Move("Sacred Blade", "Radiant", 45, 100, "Sword strike."),
    "Heavenly Blessing": Move("Heavenly Blessing", "Radiant", 0, 100, "Heals an ally."),
    "Blaze of Fury": Move("Blaze of Fury", "Radiant", 85, 100, "Fiery charge."),
    "Fiery Immolation": Move("Fiery Immolation", "Radiant", 60, 100, "Burst of fire."),
    "Phalanx": Move("Phalanx", "Steel", 0, 100, "Gain Guard if ally is Steel."),
    "Crucible of Metal": Move("Crucible of Metal", "Steel", 0, 100, "Summon Metalstorm."),
    "Frozen Slash": Move("Frozen Slash", "Cryo", 30, 90, "Slows the target."),
    "Avalanche": Move("Avalanche", "Cryo", 60, 90, "Power doubles if hit this turn."),
    "Blizzard": Move("Blizzard", "Cryo", 0, 100, "Summons hailstorm."),
    "Rimefall": Move("Rimefall", "Cryo", 80, 70, "Snowstorm."),
    "Storm's Wrath": Move("Storm's Wrath", "Storm", 70, 100, "Strong electrical attack."),
    "Galvanic Charge": Move("Galvanic Charge", "Storm", 80, 100, "Tackle with recoil."),
    "Unleash The Tempest": Move("Unleash The Tempest", "Storm", 75, 100, "Rampages."),
    "Static Discharge": Move("Static Discharge", "Storm", 55, 90, "Hits all foes."),
    "Onslaught Of Thorns": Move("Onslaught Of Thorns", "Verdant", 70, 80, "Lash of thorns."),
    "Leeching Grasp": Move("Leeching Grasp", "Verdant", 50, 100, "Heals the user."),
    "Vine Whip": Move("Vine Whip", "Verdant", 40, 100, "Quick whip."),
}
ALL_KNIGHTS = {
    "Aegis": KnightTemplate("Aegis", "Steel", 250, 40, 70, 30, ["Empowered Strike", "Guard Bash", "Phalanx", "Crucible of Metal"]),
    "Briarheart": KnightTemplate("Briarheart", "Verdant", 180, 60, 35, 50, ["Onslaught Of Thorns", "Leeching Grasp", "Vine Whip"]),
    "Sol": KnightTemplate("Sol", "Radiant", 195, 58, 40, 60, ["Sacred Blade", "Blazing Judgment", "Sunfire Burst", "Consecration", "Heavenly Blessing"]),
    "Boreas": KnightTemplate("Boreas", "Cryo", 220, 40, 60, 40, ["Frozen Slash", "Avalanche", "Blizzard", "Rimefall"]),
    "Indra": KnightTemplate("Indra", "Storm", 185, 60, 38, 80, ["Unleash The Tempest", "Static Discharge", "Storm's Wrath", "Galvanic Charge"]),
}
CO_TEAM = [
    {"template": "Sol", "custom_name": "Helios", "stats": {"hp": 195, "atk": 88, "def": 40, "spd": 70}, "ability": "Divine Power", "moves": ["Blazing Judgment", "Sunfire Burst", "Consecration", "Sacred Blade", "Heavenly Blessing"]},
    {"template": "Sol", "custom_name": "Apollo", "stats": {"hp": 195, "atk": 98, "def": 40, "spd": 60}, "ability": "Last Stand", "moves": ["Sacred Blade", "Blaze of Fury", "Fiery Immolation", "Heavenly Blessing", "Empowered Strike"]},
    {"template": "Briarheart", "custom_name": "Thorn", "stats": {"hp": 180, "atk": 90, "def": 45, "spd": 60}, "ability": "Piercing Thorns", "moves": ["Onslaught Of Thorns", "Leeching Grasp", "Vine Whip", "Empowered Strike", "Guard Bash"]},
    {"template": "Briarheart", "custom_name": "Root", "stats": {"hp": 200, "atk": 70, "def": 55, "spd": 50}, "ability": "Relentless Growth", "moves": ["Onslaught Of Thorns", "Leeching Grasp", "Vine Whip", "Empowered Strike", "Guard Bash"]},
    {"template": "Indra", "custom_name": "Tempest", "stats": {"hp": 185, "atk": 90, "def": 38, "spd": 90}, "ability": "Tempest Champion", "moves": ["Storm's Wrath", "Galvanic Charge", "Unleash The Tempest", "Static Discharge", "Empowered Strike"]},
    {"template": "Aegis", "custom_name": "Guardian", "stats": {"hp": 270, "atk": 40, "def": 90, "spd": 30}, "ability": "Bodyguard", "moves": ["Phalanx", "Guard Bash", "Empowered Strike", "Crucible of Metal", "Guard Bash"]},
]
UG_TEAM = [
    {"template": "Aegis", "custom_name": "Bastion", "stats": {"hp": 260, "atk": 50, "def": 80, "spd": 40}, "ability": "Bodyguard", "moves": ["Phalanx", "Guard Bash", "Empowered Strike", "Crucible of Metal", "Guard Bash"]},
    {"template": "Aegis", "custom_name": "Rampart", "stats": {"hp": 250, "atk": 70, "def": 80, "spd": 30}, "ability": "Reinforced", "moves": ["Empowered Strike", "Guard Bash", "Phalanx", "Crucible of Metal", "Guard Bash"]},
    {"template": "Boreas", "custom_name": "Winter", "stats": {"hp": 230, "atk": 40, "def": 80, "spd": 60}, "ability": "Frozenheart", "moves": ["Frozen Slash", "Avalanche", "Blizzard", "Rimefall", "Empowered Strike"]},
    {"template": "Boreas", "custom_name": "Glacier", "stats": {"hp": 240, "atk": 40, "def": 90, "spd": 40}, "ability": "Frozenheart", "moves": ["Frozen Slash", "Avalanche", "Blizzard", "Rimefall", "Empowered Strike"]},
    {"template": "Indra", "custom_name": "Gale", "stats": {"hp": 185, "atk": 80, "def": 38, "spd": 100}, "ability": "Grounded", "moves": ["Storm's Wrath", "Galvanic Charge", "Unleash The Tempest", "Static Discharge", "Empowered Strike"]},
    {"template": "Briarheart", "custom_name": "Hex", "stats": {"hp": 190, "atk": 65, "def": 40, "spd": 85}, "ability": "Witch Doctor", "moves": ["Onslaught Of Thorns", "Leeching Grasp", "Vine Whip", "Empowered Strike", "Guard Bash"]},
]
TEAMS = {"co": CO_TEAM, "ug": UG_TEAM}

# ... SNIP ...
