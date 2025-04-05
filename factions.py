class Faction:
    def __init__(self, name, health_mod, attack_mod, speed_mod):
        self.name = name
        self.health_mod = health_mod
        self.attack_mod = attack_mod
        self.speed_mod = speed_mod

class Player(Faction):
    def __init__(self):
        super().__init__("player", 1.0, 1.0, 1.0)

class Bandits(Faction):
    def __init__(self):
        super().__init__("bandits", 0.5, 0.5, 0.5)

class Undead(Faction):
    def __init__(self):
        super().__init__("undead", 1.0, 1.0, 1.0)

class Zombies(Faction):
    def __init__(self):
        super().__init__("zombies", 0.8, 0.9, 0.7)