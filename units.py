import pygame
import math
import random
from factions import Player, Bandits, Undead, Zombies
from collisions import check_player_collisions, check_enemy_collisions

def preload_all_animations():
    for unit_type in [Player_PeasantUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit,
                      Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank, Bandit_King,
                      Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank,
                      Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior]:
        faction = "Player" if unit_type in [Player_PeasantUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit] else \
                  "Bandits" if unit_type in [Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank, Bandit_King] else \
                  "Undead" if unit_type in [Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior] else "Zombies"
        unit = unit_type(faction, 0)
        unit.load_animations()

class Unit:
    hurt_duration = 200
    missing_spritesheets = set()

    def __init__(self, faction, x):
        self.faction = faction
        self.x = x
        self.initial_x = x
        self.y = 688
        self.health = self.base_health
        self.max_health = self.health
        self.attack_power = self.base_attack
        self.speed = self.base_speed
        self.base_attack_cooldown = self.__class__.base_attack_cooldown
        self.attack_cooldown = self.base_attack_cooldown
        self.direction = 1 if (faction == "Player" or (hasattr(faction, 'name') and faction.name == "Player")) else -1
        self.animations = {}
        self.state = "idle"
        self.frame = 0
        self.base_frame_delay = 100
        self.attack_frame_delay = self.base_attack_cooldown / 14
        self.last_update = pygame.time.get_ticks()
        self.attack_target = None
        self.is_attacking = False
        self.last_attack = 0
        self.hurt_start = None
        self.last_range_check = 0
        self.is_retreating = False
        self.scale_factor = 1.0
        # Sound initialization
        self.attack_sound = None
        self.death_sound = None
        self.is_zombie = False
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception:
            self.attack_sound = None
        self.load_animations()

    def load_animations(self):
        faction_name = self.faction if isinstance(self.faction, str) else self.faction.name
        faction_folder = faction_name.capitalize()
        spritesheet_path = f"assets/sprites/{faction_folder}/{self.name}.png"
        
        if spritesheet_path in Unit.missing_spritesheets:
            self.set_default_animations()
            return
        
        try:
            spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
            frame_width = 192
            frame_height = 192
            frames_per_state = 14
            state_rows = {"idle": 0, "run": 1, "attack": 2, "die": 3}
            self.animations = {}
            for state, row in state_rows.items():
                frames = []
                for i in range(frames_per_state):
                    x = i * frame_width
                    y = row * frame_height
                    if x + frame_width <= spritesheet.get_width() and y + frame_height <= spritesheet.get_height():
                        frame = spritesheet.subsurface((x, y, frame_width, frame_height))
                        scaled_width = int(frame_width * self.scale_factor)
                        scaled_height = int(frame_height * self.scale_factor)
                        frame = pygame.transform.smoothscale(frame, (scaled_width, scaled_height))
                        frames.append(frame)
                self.animations[state] = frames if frames else [pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))]
            self.animations["hurt"] = [pygame.transform.smoothscale(self.animations["die"][0], (int(192 * self.scale_factor), int(192 * self.scale_factor)))] if self.animations["die"] else [pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))]
        except Exception:
            Unit.missing_spritesheets.add(spritesheet_path)
            self.set_default_animations()

    def set_default_animations(self):
        default_colors = {
            "Player_Peasant": (255, 0, 0), "Player_Archer": (0, 255, 0), "Player_Warrior": (0, 0, 255), "Player_Tank": (0, 100, 100),
            "Bandit_Razor": (255, 100, 0), "Bandit_Madman": (255, 0, 100), "Bandit_Archer": (100, 255, 0), "Bandit_Tank": (100, 0, 100),
            "Bandit_King": (255, 165, 0),
            "Zombie_Melee": (255, 0, 0), "Zombie_Archer": (0, 255, 0), "Zombie_Tank": (100, 0, 100), "Zombie_Assassin": (255, 255, 0), "Zombie_Farmer": (0, 255, 255),
            "Undead_Axeman": (128, 0, 0), "Undead_King": (128, 128, 0), "Undead_Mage": (128, 0, 128), "Undead_Samurai": (0, 128, 128), "Undead_Warrior": (128, 128, 128)
        }
        color = default_colors.get(self.name, (255, 255, 255))
        default_frame = pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))
        default_frame.fill(color)
        self.animations = {state: [default_frame] for state in ["idle", "run", "attack", "die", "hurt"]}

    def get_icon(self):
        if self.animations["idle"]:
            return pygame.transform.smoothscale(self.animations["idle"][0], (192, 192))
        return pygame.Surface((192, 192))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, int(120 * self.scale_factor), int(192 * self.scale_factor))

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                    self.attack_target.take_damage(self.attack_power)
                elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                    self.attack_target.take_damage(self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

    def move(self, all_units, enemy_base, player_base, buckets, bucket_size):
        if self.state in ["attack", "die"]:
            return

        if self.direction == 1:
            new_x, new_state, target = check_player_collisions(self, buckets, bucket_size, enemy_base)
        elif self.direction == -1:
            new_x, new_state, target = check_enemy_collisions(self, buckets, bucket_size, player_base)

        self.x = new_x
        if new_state == "attack" and target:
            self.attack(target)
        else:
            self.state = new_state

    def in_attack_range(self, target):
        now = pygame.time.get_ticks()
        if now - self.last_range_check < 200:
            return False
        self.last_range_check = now
        target_x = target.x + 60 if hasattr(target, 'x') else target.x + 75
        distance = abs(self.x + (60 * self.scale_factor) - target_x)
        return distance <= self.attack_range

    def attack(self, target):
        if self.state == "die":
            return
        now = pygame.time.get_ticks()
        if now - self.last_attack >= self.attack_cooldown:
            self.state = "attack"
            self.frame = 0
            self.is_attacking = True
            self.attack_target = target
            self.last_attack = now
            if self.attack_sound:
                self.attack_sound.play()

    def take_damage(self, damage):
        if self.state == "die":
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.state = "die"
            self.frame = 0
            self.hurt_start = None
            self.is_attacking = False
            self.attack_target = None
            if self.is_zombie and self.death_sound:
                self.death_sound.play()
        elif self.state != "attack":
            self.state = "hurt"
            self.frame = 0
            self.hurt_start = pygame.time.get_ticks()

    def die(self):
        pass  # Death sound moved to take_damage

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1 and not self.is_retreating:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))

        bar_width = int(114 * self.scale_factor)
        bar_height = int(10 * self.scale_factor)
        health_ratio = self.health / self.max_health
        fill_width = bar_width * health_ratio
        bar_x = self.x + ((192 * self.scale_factor) - bar_width) // 2
        bar_y = self.y - int(20 * self.scale_factor)
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        fill_color = (0, 255, 0) if (self.faction == "Player" or (hasattr(self.faction, 'name') and self.faction.name == "Player")) else (255, 0, 0)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        hp_font = pygame.font.SysFont("Arial", int(16 * self.scale_factor))
        hp_text = hp_font.render(f"{int(self.health)}/{self.max_health}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + (bar_width - hp_text.get_width()) // 2, bar_y - int(20 * self.scale_factor)))

# Player Units
class Player_PeasantUnit(Unit):
    name = "Player_Peasant"
    base_health = 50
    base_attack = 20
    base_speed = 1.0
    base_attack_cooldown = 1000
    cost = 20
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_fist.ogg")
        except Exception:
            self.attack_sound = None

class Player_ArcherUnit(Unit):
    name = "Player_Archer"
    base_health = 30
    base_attack = 15
    base_speed = 1.4
    base_attack_cooldown = 1000
    cost = 30
    attack_range = 250

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                arrow_start_x = self.x + int(115 * self.scale_factor)
                arrow_start_y = self.y + int(105 * self.scale_factor)
                if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
                elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

class Player_WarriorUnit(Unit):
    name = "Player_Warrior"
    base_health = 80
    base_attack = 25
    base_speed = 1.15
    base_attack_cooldown = 1000
    cost = 50
    attack_range = 125

class Player_TankUnit(Unit):
    name = "Player_Tank"
    base_health = 150
    base_attack = 10
    base_speed = 0.5
    base_attack_cooldown = 1500
    cost = 60
    attack_range = 125

# Bandit Units
class Bandit_Razor(Unit):
    name = "Bandit_Razor"
    base_health = 40
    base_attack = 25
    base_speed = 1.5
    base_attack_cooldown = 800
    cost = 30
    attack_range = 125

class Bandit_Madman(Unit):
    name = "Bandit_Madman"
    base_health = 60
    base_attack = 20
    base_speed = 1.2
    base_attack_cooldown = 1000
    cost = 25
    attack_range = 125

class Bandit_Archer(Unit):
    name = "Bandit_Archer"
    base_health = 30
    base_attack = 15
    base_speed = 1.4
    base_attack_cooldown = 1000
    cost = 30
    attack_range = 250

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                arrow_start_x = self.x + int(77 * self.scale_factor)
                arrow_start_y = self.y + int(105 * self.scale_factor)
                if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
                elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

class Bandit_Tank(Unit):
    name = "Bandit_Tank"
    base_health = 150
    base_attack = 10
    base_speed = 0.5
    base_attack_cooldown = 1500
    cost = 60
    attack_range = 125

class Bandit_King(Unit):
    name = "Bandit_King"
    base_health = 1000
    base_attack = 20
    base_speed = 2
    base_attack_cooldown = 1000
    cost = 0
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.y = 592

    def load_animations(self):
        faction_name = self.faction if isinstance(self.faction, str) else self.faction.name
        faction_folder = faction_name.capitalize()
        spritesheet_path = f"assets/sprites/{faction_folder}/{self.name}.png"
        
        if spritesheet_path in Unit.missing_spritesheets:
            self.set_default_animations()
            return
        
        try:
            spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
            frame_width = 192
            frame_height = 192
            frames_per_state = 14
            state_rows = {"idle": 0, "run": 1, "attack": 2, "die": 3}
            self.animations = {}
            for state, row in state_rows.items():
                frames = []
                for i in range(frames_per_state):
                    x = i * frame_width
                    y = row * frame_height
                    if x + frame_width <= spritesheet.get_width() and y + frame_height <= spritesheet.get_height():
                        frame = spritesheet.subsurface((x, y, frame_width, frame_height))
                        frame = pygame.transform.smoothscale(frame, (288, 288))
                        frames.append(frame)
                self.animations[state] = frames if frames else [pygame.Surface((288, 288))]
            self.animations["hurt"] = [pygame.transform.smoothscale(self.animations["die"][0], (288, 288))] if self.animations["die"] else [pygame.Surface((288, 288))]
        except Exception:
            Unit.missing_spritesheets.add(spritesheet_path)
            self.set_default_animations()

    def set_default_animations(self):
        default_frame = pygame.Surface((288, 288))
        default_frame.fill((255, 165, 0))
        self.animations = {state: [default_frame] for state in ["idle", "run", "attack", "die", "hurt"]}

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 180, 288)

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1 and not self.is_retreating:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))

        bar_width = 171
        bar_height = 15
        health_ratio = self.health / self.max_health
        fill_width = bar_width * health_ratio
        bar_x = self.x + (288 - bar_width) // 2
        bar_y = self.y - 30
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        fill_color = (255, 0, 0)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        hp_font = pygame.font.SysFont("Arial", 24)
        hp_text = hp_font.render(f"{int(self.health)}/{self.max_health}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + (bar_width - hp_text.get_width()) // 2, bar_y - 30))

# Zombie Units
class Zombie_Melee(Unit):
    name = "Zombie_Melee"
    base_health = 50
    base_attack = 20
    base_speed = 1.0
    base_attack_cooldown = 1000
    cost = 20
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.is_zombie = True
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/Units/Zombie_die.ogg")
        except Exception:
            self.death_sound = None

class Zombie_Archer(Unit):
    name = "Zombie_Archer"
    base_health = 30
    base_attack = 15
    base_speed = 1.4
    base_attack_cooldown = 1000
    cost = 30
    attack_range = 250

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.is_zombie = True
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/Units/Zombie_die.ogg")
        except Exception:
            self.death_sound = None

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                arrow_start_x = self.x + int(77 * self.scale_factor)
                arrow_start_y = self.y + int(105 * self.scale_factor)
                if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
                elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                    return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

class Zombie_Assassin(Unit):
    name = "Zombie_Assassin"
    base_health = 20
    base_attack = 30
    base_speed = 2.0
    base_attack_cooldown = 500
    cost = 40
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.is_zombie = True
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/Units/Zombie_die.ogg")
        except Exception:
            self.death_sound = None

class Zombie_Farmer(Unit):
    name = "Zombie_Farmer"
    base_health = 60
    base_attack = 15
    base_speed = 0.9
    base_attack_cooldown = 1200
    cost = 25
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.is_zombie = True
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/Units/Zombie_die.ogg")
        except Exception:
            self.death_sound = None

class Zombie_Tank(Unit):
    name = "Zombie_Tank"
    base_health = 150
    base_attack = 10
    base_speed = 0.5
    base_attack_cooldown = 1500
    cost = 60
    attack_range = 125

    def __init__(self, faction, x):
        super().__init__(faction, x)
        self.is_zombie = True
        try:
            self.death_sound = pygame.mixer.Sound("assets/sounds/Units/Zombie_die.ogg")
        except Exception:
            self.death_sound = None

# Undead Units
class Undead_Axeman(Unit):
    name = "Undead_Axeman"
    base_health = 70
    base_attack = 25
    base_speed = 1.0
    base_attack_cooldown = 1000
    cost = 35
    attack_range = 125

class Undead_King(Unit):
    name = "Undead_King"
    base_health = 100
    base_attack = 30
    base_speed = 0.8
    base_attack_cooldown = 1200
    cost = 50
    attack_range = 150

class Undead_Mage(Unit):
    name = "Undead_Mage"
    base_health = 50
    base_attack = 25
    base_speed = 1.0
    base_attack_cooldown = 1500
    cost = 50
    attack_range = 200

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                magicball_start_x = self.x + int(77 * self.scale_factor)
                magicball_start_y = self.y + int(105 * self.scale_factor)
                if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                    return MagicBall(magicball_start_x, magicball_start_y, self.direction, self.attack_target, self.attack_power)
                elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                    return MagicBall(magicball_start_x, magicball_start_y, self.direction, self.attack_target, self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

class Undead_Samurai(Unit):
    name = "Undead_Samurai"
    base_health = 60
    base_attack = 35
    base_speed = 1.3
    base_attack_cooldown = 900
    cost = 40
    attack_range = 125

class Undead_Warrior(Unit):
    name = "Undead_Warrior"
    base_health = 80
    base_attack = 20
    base_speed = 1.1
    base_attack_cooldown = 1000
    cost = 30
    attack_range = 125

# Cart Unit
class CartUnit:
    def __init__(self, x, y, target_x, faction="Bandits"):
        self.faction = faction
        self.x = x
        self.y = 688
        self.target_x = target_x
        self.speed = -1.5
        self.moving = True
        try:
            self.sprite = pygame.image.load("assets/images/Cart.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (150, 150))
        except Exception:
            self.sprite = pygame.Surface((150, 150))
            self.sprite.fill((139, 69, 19))

    def update(self):
        if self.moving and self.x > self.target_x:
            self.x += self.speed

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

# Projectile Classes
class Arrow:
    def __init__(self, x, y, direction, target, damage, max_distance=1000):
        self.x = x
        self.y = y
        self.start_x = x
        self.direction = direction
        self.target = target
        self.damage = damage
        self.active = True
        self.max_distance = max_distance

        if hasattr(target, 'x') and hasattr(target, 'y'):
            self.target_x = target.x + (60 * getattr(target, 'scale_factor', 1.0))
            self.target_y = target.y + (102 * getattr(target, 'scale_factor', 1.0))
        else:
            self.target_x = target.x + (75 if direction == 1 else 150)
            self.target_y = target.y + 150

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.gravity = 0.2
        travel_time = max(20, min(60, int(abs(dx) / 10))) + random.randint(-5, 5)
        self.velocity_x = dx / travel_time if dx != 0 else 3 * direction
        self.velocity_y = (dy - 0.5 * self.gravity * travel_time * (travel_time - 1)) / travel_time

        try:
            self.sprite = pygame.image.load("assets/images/arrow.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (32, 16))
        except Exception:
            self.sprite = pygame.Surface((32, 16))
            self.sprite.fill((255, 255, 255))

        self.rotated_sprite = self.sprite

    def update(self, all_units):
        if not self.active:
            return True

        if not self.target or (hasattr(self.target, 'state') and self.target.state == "die") or \
           (hasattr(self.target, 'health') and self.target.health <= 0):
            self.active = False
            return True

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += self.gravity

        traveled_distance = abs(self.x - self.start_x)
        if traveled_distance > self.max_distance:
            self.active = False
            return True

        angle = math.degrees(math.atan2(-self.velocity_y, self.velocity_x))
        self.rotated_sprite = pygame.transform.rotate(self.sprite, angle)

        arrow_rect = pygame.Rect(self.x - 16, self.y - 8, 32, 16)
        target_rect = self.target.get_rect()

        if arrow_rect.colliderect(target_rect):
            if self.check_pixel_collision(self.target):
                if (hasattr(self.target, 'state') and self.target.state != "die") or \
                   (hasattr(self.target, 'health') and self.target.health > 0):
                    self.target.take_damage(self.damage)
                self.active = False
                return True
        return False

    def check_pixel_collision(self, target):
        if hasattr(target, 'animations') and target.state in target.animations:
            frame = target.animations[target.state][target.frame]
            if target.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            mask = pygame.mask.from_surface(frame)
            arrow_mask = pygame.mask.from_surface(self.rotated_sprite)
            offset_x = int(self.x - target.x)
            offset_y = int(self.y - target.y)
            overlap = mask.overlap(arrow_mask, (offset_x, offset_y))
            return overlap is not None
        return True

    def draw(self, screen):
        if self.active:
            screen.blit(self.rotated_sprite, (self.x - 16, self.y - 8))

class MagicBall:
    def __init__(self, x, y, direction, target, damage, max_distance=1000):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.direction = direction
        self.target = target
        self.damage = damage
        self.active = True
        self.max_distance = max_distance
        self.speed = 5

        if hasattr(target, 'x') and hasattr(target, 'y'):
            target_x = target.x + (60 * getattr(target, 'scale_factor', 1.0))
            target_y = target.y + (102 * getattr(target, 'scale_factor', 1.0))
        else:
            target_x = target.x + (75 if direction == 1 else 150)
            target_y = target.y + 150
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            self.vx = self.speed * (dx / distance)
            self.vy = self.speed * (dy / distance)
        else:
            self.vx = 0
            self.vy = 0
            self.active = False

        try:
            self.sprite = pygame.image.load("assets/images/magicball.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (32, 32))
        except Exception:
            self.sprite = pygame.Surface((32, 32))
            self.sprite.fill((128, 0, 128))

        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.rotated_sprite = pygame.transform.rotate(self.sprite, angle)

    def update(self, all_units):
        if not self.active:
            return True

        self.x += self.vx
        self.y += self.vy

        traveled_distance = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)
        if traveled_distance > self.max_distance:
            self.active = False
            return True

        if self.target and ((hasattr(self.target, 'state') and self.target.state != "die") or
                           (hasattr(self.target, 'health') and self.target.health > 0)):
            target_rect = self.target.get_rect()
            magicball_rect = pygame.Rect(self.x - 16, self.y - 16, 32, 32)
            if magicball_rect.colliderect(target_rect):
                self.target.take_damage(self.damage)
                self.active = False
                return True
        else:
            self.active = False
            return True

        return False

    def draw(self, screen):
        if self.active:
            screen.blit(self.rotated_sprite, (self.x - 16, self.y - 16))