from units import (
    Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank,
    Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank,
    Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior
)
import random

class Level:
    def __init__(self, level_number):
        self.level_number = level_number
        self.faction, self.units = self.define_level_units()

    def define_level_units(self):
        if 1 <= self.level_number <= 5:
            return "Bandits", [Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank]
        elif 6 <= self.level_number <= 10:
            return "Zombies", [Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank]
        elif 11 <= self.level_number <= 20:
            return "Undead", [Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior]
        else:
            raise ValueError(f"Invalid level number: {self.level_number}")

    def get_next_enemy_unit(self):
        return random.choice(self.units) if self.units else None