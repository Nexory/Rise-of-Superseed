import pygame
import random
from levels import Level
from buildings import Base
from ui import UI
from units import Unit, Player_ArcherUnit, Bandit_King, Bandit_Razor, CartUnit
from factions import Player, Bandits, Undead, Zombies
import js
import asyncio

class SeedDrop:
    def __init__(self, x, y, value):
        self.x = x + random.uniform(-20, 20)
        self.y = 920 - 40
        self.value = value
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 5000
        self.alpha = 255
        try:
            self.sprite = pygame.image.load("assets/images/seed.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (51, 51))
        except Exception as e:
            js.console.log(f"Failed to load seed sprite: assets/images/seed.png - {str(e)}")
            self.sprite = pygame.Surface((51, 51))
            self.sprite.fill((249, 249, 242))  # Fallback off-white surface

    def update(self):
        elapsed = pygame.time.get_ticks() - self.creation_time
        if elapsed > self.lifetime - 1000:
            self.alpha = max(0, 255 * (self.lifetime - elapsed) / 1000)
            self.sprite.set_alpha(int(self.alpha))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

    def is_expired(self):
        return pygame.time.get_ticks() - self.creation_time >= self.lifetime

class Tower:
    def __init__(self, x, y, sprite_path, base_width, base_height):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (base_width, base_height))
        except Exception as e:
            js.console.log(f"Failed to load tower sprite: {sprite_path} - {str(e)}")
            self.sprite = pygame.Surface((base_width, base_height))
            self.sprite.fill((0, 0, 255))  # Fallback blue surface

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class Wall:
    def __init__(self, x, y, sprite_path):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            orig_width, orig_height = self.sprite.get_size()
            new_width = int(orig_width * 0.75)
            new_height = int(orig_height * 0.75)
            self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        except Exception as e:
            js.console.log(f"Failed to load wall sprite: {sprite_path} - {str(e)}")
            self.sprite = pygame.Surface((75, 225))
            self.sprite.fill((150, 150, 150))  # Fallback gray surface

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class Game:
    passive_income = 0.1
    BUCKET_SIZE = 400
    FACTION_MAP = {
        "Player": Player(),
        "Bandits": Bandits(),
        "Undead": Undead(),
        "Zombies": Zombies()
    }

    def __init__(self, level_number, main_menu, screen, clock):
        self.player_faction = "Player"
        self.level = Level(level_number)
        self.enemy_faction = self.level.faction
        self.seeds = 50
        self.units = []
        self.enemy_units = []
        self.seed_drops = []
        self.arrows = []
        self.xp = 0
        self.max_xp = 100
        self.level_up_available = False
        self.level_up_button = pygame.Rect(1920 // 2 - 100, 140, 200, 40)
        self.main_menu = main_menu
        self.screen = screen
        self.clock = clock
        self.menu_open = False
        self.menu_button = pygame.Rect(1920 - 180, 20, 60, 40)
        self.menu_options = {
            "Back to Menu": pygame.Rect(1920 - 180, 70, 150, 40),
            "Options": pygame.Rect(1920 - 180, 120, 150, 40),
            "Exit Game": pygame.Rect(1920 - 180, 170, 150, 40)
        }
        self.show_options_submenu = False
        self.options_submenu_buttons = {
            "Toggle Fullscreen": pygame.Rect(1920 // 2 - 75, 1080 // 2 - 20, 150, 40),
            "Back": pygame.Rect(1920 // 2 - 75, 1080 // 2 + 30, 150, 40)
        }
        self.selected_unit = None

        # Battlefield background
        self.static_surface = pygame.Surface((1920, 1040)).convert()
        try:
            battlefield = pygame.image.load("assets/backgrounds/battlefield.png").convert()
            orig_height = battlefield.get_height()
            crop_height = int(orig_height * 0.95)
            battlefield = battlefield.subsurface((0, 0, battlefield.get_width(), crop_height))
            self.static_surface.blit(pygame.transform.scale(battlefield, (1920, 880)), (0, 0))
        except Exception as e:
            js.console.log(f"Failed to load battlefield background: assets/backgrounds/battlefield.png - {str(e)}")
            self.static_surface.fill((0, 100, 0))  # Fallback green surface
        pygame.draw.rect(self.static_surface, (14, 39, 59), (0, 880, 1920, 160))

        # Walls and base with corrected relative paths
        self.player_wall_back = Wall(0, 880-225, "assets/buildings/Player/Skin 1/player_wall_back.png")
        self.player_base = Base(x=125, y=880-300, health=Base.base_health,
                               sprite_path="assets/buildings/Player/Skin 1/player_base.png", is_player=True)
        self.player_wall = Wall(-50, 880-225, "assets/buildings/Player/Skin 1/player_wall.png")
        self.player_tower = None
        self.enemy_base = Base(x=1920-250, y=880-300, health=1000,
                              sprite_path="assets/buildings/Enemy/Zombies/enemy_base.png", is_player=False)


        self.ui = UI(self, 1920)
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.game_over = False
        self.won = False
        self.fade_alpha = 0
        self.fade_speed = 5
        self.return_button = pygame.Rect(1920 // 2 - 100, 880 // 2 + 100, 200, 60)
        
        self.show_intro = self.level.level_number == 1 and self.main_menu.max_level < 2
        self.show_end_story = False
        self.okay_button = pygame.Rect(0, 0, 200, 60)
        
        self.bandit_king = None
        self.show_bandit_intro = False
        self.units_moving_back = False
        self.king_moving = False
        self.enemy_spawns_stopped = False
        self.cart = None
        self.show_bandit_surrender = False
        self.show_surrender_part_two = False
        self.show_king_threat = False

        self.start_time = pygame.time.get_ticks()
        self.main_menu.achievements.check_achievements("game_started", {})
        self.frame_count = 0
        self.surrender_triggered = False
        self.surrender_timer = None
        self.scale_factor = 1.0
        
        try:
            self.menu_button_bg = pygame.image.load("assets/ui/ui_buttons.png").convert_alpha()
        except Exception as e:
            js.console.log(f"Failed to load menu button background: assets/ui/ui_buttons.png - {str(e)}")
            self.menu_button_bg = pygame.Surface((60, 40))
            self.menu_button_bg.fill((147, 208, 207))  # Fallback cyan surface

        from eventhandler import EventHandler
        self.event_handler = EventHandler(self)
        self.running = True  # Added to ensure run loop works

    def spawn_unit(self, unit_type):
        if self.seeds >= unit_type.cost:
            self.seeds -= unit_type.cost
            spawn_x = 100
            unit_width = 120
            for existing_unit in self.units:
                if abs(spawn_x - existing_unit.x) < unit_width and existing_unit.state != "die":
                    spawn_x -= unit_width
            new_unit = unit_type(self.player_faction, spawn_x)
            faction = self.FACTION_MAP.get(self.player_faction, Player())
            new_unit.max_health *= faction.health_mod
            new_unit.health = new_unit.max_health
            new_unit.attack_power *= faction.attack_mod
            new_unit.speed *= faction.speed_mod
            unit_name = unit_type.__name__.replace("Player_", "").replace("Unit", "")
            upgrades = self.main_menu.unit_upgrades.get(unit_name, {})
            health_increase = upgrades.get("Health", {}).get("level", 0) * upgrades.get("Health", {}).get("increase", 0)
            damage_increase = upgrades.get("Damage", {}).get("level", 0) * upgrades.get("Damage", {}).get("increase", 0)
            attack_speed_level = upgrades.get("Attack Speed", {}).get("level", 0)
            increase_factor = upgrades.get("Attack Speed", {}).get("increase", 0.075)
            movement_speed_increase = upgrades.get("Movement Speed", {}).get("level", 0) * upgrades.get("Movement Speed", {}).get("increase", 0)
            
            new_unit.max_health += health_increase
            new_unit.health = new_unit.max_health
            new_unit.attack_power += damage_increase
            min_cooldown = 200
            new_unit.attack_cooldown = max(min_cooldown, new_unit.base_attack_cooldown / (1 + attack_speed_level * increase_factor))
            new_unit.attack_frame_delay = new_unit.attack_cooldown / 14
            new_unit.speed += movement_speed_increase
            
            self.units.append(new_unit)
            self.main_menu.achievements.check_achievements("unit_spawned", {"unit": new_unit})
            js.console.log(f"Spawned {unit_type.__name__}: Health={new_unit.max_health:.1f}, Damage={new_unit.attack_power:.1f}, Speed={new_unit.speed:.1f}, Attack Cooldown={new_unit.attack_cooldown}")
            return new_unit

    def spawn_enemy_unit(self):
        if self.enemy_spawns_stopped:
            js.console.log("Enemy spawn blocked after base destroyed or king spawned")
            return
        unit_type = self.level.get_next_enemy_unit()
        if not unit_type:
            return
        spawn_x = 1920 - 100
        unit_width = 120
        for existing_unit in self.enemy_units:
            if abs(spawn_x - existing_unit.x) < unit_width and existing_unit.state != "die":
                spawn_x += unit_width
        new_unit = unit_type(self.enemy_faction, spawn_x)
        faction = self.FACTION_MAP.get(self.enemy_faction, Zombies())
        new_unit.max_health *= faction.health_mod
        new_unit.health = new_unit.max_health
        new_unit.attack_power *= faction.attack_mod
        new_unit.speed *= faction.speed_mod
        self.enemy_units.append(new_unit)
        js.console.log(f"Spawned enemy {unit_type.__name__}: Health={new_unit.max_health:.1f}, Damage={new_unit.attack_power:.1f}, Speed={new_unit.speed:.1f}")

    def spawn_bandit_king(self):
        self.bandit_king = Bandit_King(self.enemy_faction, 1920 - 250)
        self.enemy_units.append(self.bandit_king)
        self.show_bandit_intro = True
        self.units_moving_back = True
        self.king_moving = True
        self.enemy_spawns_stopped = True
        self.surrender_triggered = False
        js.console.log(f"Bandit King spawned at x={self.bandit_king.x}")

    def spawn_cart_and_razor(self):
        razor_unit = Bandit_Razor(self.enemy_faction, 1920 - 100)
        razor_unit.speed = 1.5
        self.enemy_units.append(razor_unit)
        js.console.log(f"Spawned Bandit Razor at x={razor_unit.x} with speed={razor_unit.speed}")

        target_x = self.bandit_king.x - 50
        self.cart = CartUnit(2000, 880 - 150, target_x)
        js.console.log(f"Spawned Cart at x={self.cart.x} with speed={self.cart.speed}")

    def apply_upgrade(self, unit, upgrade_type):
        unit_name = unit.__class__.__name__.replace("Player_", "").replace("Unit", "")
        upgrade_data = self.main_menu.unit_upgrades.get(unit_name, {}).get(upgrade_type.capitalize())
        if not upgrade_data or unit.state == "die":
            return
        cost = upgrade_data["cost"]
        if self.main_menu.secured_seeds >= cost:
            self.main_menu.secured_seeds -= cost
            upgrade_data["level"] += 1
            level = upgrade_data["level"]
            if upgrade_type == "health":
                unit.max_health += upgrade_data["increase"]
                unit.health += upgrade_data["increase"]
            elif upgrade_type == "damage":
                unit.attack_power += upgrade_data["increase"]
            elif upgrade_type == "attack speed":
                increase_factor = upgrade_data["increase"]
                min_cooldown = 200
                new_cooldown = max(min_cooldown, unit.base_attack_cooldown / (1 + level * increase_factor))
                unit.attack_cooldown = new_cooldown
                unit.attack_frame_delay = new_cooldown / 14
            elif upgrade_type == "movement speed":
                unit.speed += upgrade_data["increase"]
            self.main_menu.save_player_data()
            self.main_menu.achievements.check_achievements("upgrade_applied", {"upgrade_type": upgrade_type})

    def get_seed_reward(self, unit):
        return {"Player_Peasant": 5, "Player_Archer": 10, "Player_Warrior": 15, "Player_Tank": 20,
                "Zombie_Melee": 5, "Zombie_Archer": 10, "Zombie_Tank": 20, "Zombie_Assassin": 15,
                "Bandit_King": 50}.get(unit.name, 5)

    def get_xp_reward(self, unit):
        return {"Player_Peasant": 10, "Player_Archer": 15, "Player_Warrior": 20, "Player_Tank": 25,
                "Zombie_Melee": 10, "Zombie_Archer": 15, "Zombie_Tank": 25, "Zombie_Assassin": 20,
                "Bandit_King": 100}.get(unit.name, 10)

    def get_buckets(self, units):
        buckets = {}
        for unit in units:
            if unit.state != "die" and -192 <= unit.x <= 1920:
                bucket_x = max(0, min(int(unit.x // self.BUCKET_SIZE), 1920 // self.BUCKET_SIZE))
                buckets.setdefault(bucket_x, []).append(unit)
        return buckets

    def find_nearest_target(self, unit, all_units, base):
        bucket_x = int(unit.x // self.BUCKET_SIZE)
        check_buckets = [max(0, bucket_x - 1), bucket_x, min(1920 // self.BUCKET_SIZE, bucket_x + 1)]
        buckets = self.get_buckets(all_units)
        
        nearest = None
        min_dist = unit.attack_range
        for b in check_buckets:
            if b in buckets:
                for other in buckets[b]:
                    if other is not unit and other.state != "die" and unit.faction != other.faction:
                        dist = abs(unit.x - other.x)
                        if dist < min_dist:
                            min_dist = dist
                            nearest = other
        
        base_dist = abs(unit.x - (base.get_rect().left if unit.direction == 1 else base.get_rect().right))
        if base_dist < min_dist and base.health > 0 and "tower" not in base.sprite_path.lower():
            nearest = base
        return nearest

    def is_paused_by_event(self):
        return (self.show_intro or self.show_end_story or self.show_bandit_intro or 
                self.show_surrender_part_two or self.show_king_threat)

    def update(self):
        if self.game_over:
            self.fade_alpha = min(self.fade_alpha + self.fade_speed, 255)
            return True

        if self.menu_open:
            return True

        if not self.is_paused_by_event():
            self.seeds += self.passive_income

        all_units = self.units + self.enemy_units

        self.event_handler.update()

        if self.is_paused_by_event():
            return True

        if self.bandit_king:
            js.console.log(f"Bandit King status - state: {self.bandit_king.state}, "
                           f"health: {self.bandit_king.health}/{self.bandit_king.max_health}, "
                           f"x: {self.bandit_king.x}, in enemy_units: {self.bandit_king in self.enemy_units}")

        if self.cart and self.cart.moving:
            razor_unit = next((unit for unit in self.enemy_units if isinstance(unit, Bandit_Razor)), None)
            if razor_unit and self.bandit_king:
                razor_dist = abs(razor_unit.x - self.bandit_king.x)
                cart_dist = abs(self.cart.x - self.cart.target_x)
                js.console.log(f"Cart x={self.cart.x}, target_x={self.cart.target_x}, dist={cart_dist}, "
                               f"Razor x={razor_unit.x}, King x={self.bandit_king.x}, dist={razor_dist}")
                if razor_dist < 150 and cart_dist < 20:
                    self.cart.x = self.cart.target_x
                    self.cart.moving = False
                    self.show_surrender_part_two = True
                    js.console.log("Cart stopped and surrender part two triggered")
            self.cart.update()

        if self.bandit_king and not self.surrender_triggered:
            if (self.bandit_king.health <= self.bandit_king.max_health * 0.1 and 
                self.main_menu.max_level <= 5):
                js.console.log("Surrender triggered: Bandit King at 10% health")
                self.show_bandit_surrender = True
                self.surrender_triggered = True
                self.arrows = []
                self.spawn_cart_and_razor()
                self.cart.moving = True
                for unit in self.units + [self.bandit_king]:
                    if unit.state != "die":
                        unit.state = "idle"
                        unit.is_attacking = False
                        unit.attack_target = None
                        js.console.log(f"Unit {unit.name} set to idle")

        self.event_handler.handle_units_moving_back()
        self.event_handler.handle_king_moving()

        for unit in self.units[:]:
            if -192 <= unit.x <= 1920:
                if self.cart and (self.cart.moving or self.show_surrender_part_two) or self.king_moving:
                    unit.state = "idle"
                    unit.is_attacking = False
                    unit.attack_target = None
                    unit.update_animation()
                else:
                    arrow = unit.update_animation()
                    if arrow:
                        self.arrows.append(arrow)
                    unit.move(all_units, self.enemy_base, self.player_base, self.get_buckets(all_units), self.BUCKET_SIZE)
                    if unit.x >= 1920 - 120:
                        unit.x = 1920 - 120
                        unit.state = "idle"
                    if self.bandit_king and unit.in_attack_range(self.bandit_king):
                        unit.attack(self.bandit_king)
                    elif unit.in_attack_range(self.enemy_base):
                        unit.attack(self.enemy_base)
                    else:
                        nearest_target = self.find_nearest_target(unit, all_units, self.enemy_base)
                        if nearest_target:
                            unit.attack(nearest_target)

        self.units[:] = [unit for unit in self.units if not (unit.state == "die" and unit.frame >= len(unit.animations["die"]) - 1)]

        for enemy in self.enemy_units[:]:
            if enemy == self.bandit_king:
                js.console.log(f"Updating Bandit King: state={enemy.state}, x={enemy.x}")
            if -192 <= enemy.x <= 1920:
                if (self.cart and (self.cart.moving or self.show_surrender_part_two) or self.king_moving) and not isinstance(enemy, Bandit_Razor):
                    enemy.state = "idle"
                    enemy.is_attacking = False
                    enemy.attack_target = None
                    enemy.update_animation()
                else:
                    arrow = enemy.update_animation()
                    if arrow:
                        self.arrows.append(arrow)
                    enemy.move(all_units, self.enemy_base, self.player_base, self.get_buckets(all_units), self.BUCKET_SIZE)
                    if enemy.x <= 120:
                        enemy.x = 120
                        enemy.state = "idle"
                    if enemy.in_attack_range(self.player_base):
                        enemy.attack(self.player_base)
                    else:
                        nearest_target = self.find_nearest_target(enemy, all_units, self.player_base)
                        if nearest_target:
                            enemy.attack(nearest_target)

        dead_enemies = [enemy for enemy in self.enemy_units if enemy.state == "die" and enemy.frame >= len(enemy.animations["die"]) - 1]
        for enemy in dead_enemies:
            if enemy == self.bandit_king:
                js.console.log("Bandit King being removed from enemy_units due to death")
                self.bandit_king = None
                if self.level.level_number == 5:
                    self.handle_level_completion()
            self.seeds += self.get_seed_reward(enemy)
            self.xp += self.get_xp_reward(enemy)
            for _ in range(self.get_seed_reward(enemy)):
                self.seed_drops.append(SeedDrop(enemy.x, enemy.y, 1))
            self.main_menu.achievements.check_achievements("unit_killed", {"unit": enemy, "killer": "Player"})
        self.enemy_units[:] = [enemy for enemy in self.enemy_units if enemy not in dead_enemies]

        self.seed_drops[:] = [drop for drop in self.seed_drops if not drop.is_expired()]
        for drop in self.seed_drops:
            drop.update()

        self.arrows[:] = [arrow for arrow in self.arrows if not arrow.update(all_units)]

        now = pygame.time.get_ticks()
        if not self.enemy_spawns_stopped and now - self.last_enemy_spawn >= 3000:
            self.spawn_enemy_unit()
            self.last_enemy_spawn = now

        if self.xp >= self.max_xp:
            self.level_up_available = True
        else:
            self.level_up_available = False

        if self.player_base.health <= 0:
            self.game_over = True
            self.won = False
        elif self.enemy_base.health <= 0:
            if self.level.level_number == 5 and self.bandit_king is None:
                for enemy in self.enemy_units:
                    enemy.state = "die"
                    enemy.frame = 0
                self.enemy_units = []
                self.enemy_spawns_stopped = True
                js.console.log("Enemy base destroyed, spawning Bandit King")
                self.spawn_bandit_king()
            elif self.level.level_number != 5:
                for enemy in self.enemy_units:
                    enemy.state = "die"
                    enemy.frame = 0
                self.enemy_units = []
                self.enemy_spawns_stopped = True
                self.handle_level_completion()

        return True

    async def run(self):
        # Set the screen to yellow to confirm rendering works
        self.screen.fill((255, 255, 0))
        pygame.display.flip()
        
        # Main game loop
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                
                ### Event Handling ###
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.event_handler.handle_events(event)
                        result = self.ui.handle_event(event)
                        if result:
                            self.spawn_unit(result)
                
                ### Update Game State ###
                self.update()

                ### Draw to Screen ###
                self.draw(self.screen)
                
                ### Update Display and Yield ###
                pygame.display.flip()
                await asyncio.sleep(0.001)  # Yield control to the browser's event loop
                
                ### Frame Rate Control ###
                self.clock.tick(60)  # Cap at 60 FPS
            
            except Exception as e:
                break

    def draw(self, screen):
        screen.blit(self.static_surface, (0, 0))
        self.player_wall_back.draw(screen)
        for unit in self.units + self.enemy_units:
            if -192 <= unit.x <= 1920:
                unit.draw(screen)
                if unit == self.selected_unit:
                    pygame.draw.rect(screen, (255, 255, 0), unit.get_rect(), 2)
        self.player_base.draw(screen)
        self.player_wall.draw(screen)
        if self.player_tower:
            self.player_tower.draw(screen)
        self.enemy_base.draw(screen)
        for drop in self.seed_drops:
            drop.draw(screen)
        for arrow in self.arrows:
            arrow.draw(screen)
        if self.cart:
            self.cart.draw(screen)
        
        self.ui.draw(screen)

        # Use TrueType fonts with increased size for clarity
        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 28)  # Increased from 24
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 24)  # Increased from 20
        except Exception as e:
            print(f"Failed to load fonts in Game: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 28, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 24)
        
        self.event_handler.draw(screen)

        if self.game_over:
            overlay = pygame.Surface((1920, 1040))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.fade_alpha)
            screen.blit(overlay, (0, 0))
            if self.fade_alpha >= 255:
                result_text = FONT_CTA.render("Victory" if self.won else "Defeat", True, (255, 255, 255))
                screen.blit(result_text, (1920 // 2 - result_text.get_width() // 2, 880 // 2 - 50))
                pygame.draw.rect(screen, (147, 208, 207), self.return_button)
                return_text = FONT_CTA.render("Return to Menu", True, (249, 249, 242))
                screen.blit(return_text, (self.return_button.x + 20, self.return_button.y + 20))
        elif not self.show_intro and not self.show_end_story and not self.show_bandit_intro and not self.show_surrender_part_two and not self.show_king_threat:
            menu_bg = pygame.transform.scale(self.menu_button_bg, (self.menu_button.width, self.menu_button.height))
            screen.blit(menu_bg, (self.menu_button.x, self.menu_button.y))
            menu_text = FONT_CTA.render("Menu", True, (249, 249, 242))
            screen.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + (self.menu_button.height - menu_text.get_height()) // 2))

            if self.menu_open:
                for option, rect in self.menu_options.items():
                    pygame.draw.rect(screen, (128, 131, 134), rect)
                    text = FONT_BODY.render(option, True, (249, 249, 242))
                    screen.blit(text, (rect.x + 10, rect.y + 10))
                
                if self.show_options_submenu:
                    options_window_rect = pygame.Rect(1920 // 2 - 90, 1080 // 2 - 50, 180, 120)
                    pygame.draw.rect(screen, (14, 39, 59), options_window_rect)
                    pygame.draw.rect(screen, (147, 208, 207), options_window_rect, 2)
                    for option, rect in self.options_submenu_buttons.items():
                        pygame.draw.rect(screen, (128, 131, 134), rect)
                        text = FONT_BODY.render(option, True, (249, 249, 242))
                        screen.blit(text, (rect.x + 10, rect.y + 10))

            level_text = FONT_BODY.render(f"Level: {self.level.level_number} - {self.enemy_faction}", True, (249, 249, 242))
            screen.blit(level_text, (1920 // 2 - level_text.get_width() // 2, 20))

            xp_bar_width = 200
            xp_bar_height = 20
            xp_ratio = min(self.xp / self.max_xp, 1.0)
            xp_fill_width = xp_bar_width * xp_ratio
            xp_bar_rect = pygame.Rect(1920 // 2 - xp_bar_width // 2, 100, xp_bar_width, xp_bar_height)
            pygame.draw.rect(screen, (128, 131, 134), xp_bar_rect)
            pygame.draw.rect(screen, (0, 255, 255), (xp_bar_rect.x, xp_bar_rect.y, xp_fill_width, xp_bar_height))
            xp_text = FONT_BODY.render(f"XP: {int(self.xp)}/{int(self.max_xp)}", True, (249, 249, 242))
            screen.blit(xp_text, (xp_bar_rect.x + xp_bar_width // 2 - xp_text.get_width() // 2, xp_bar_rect.y - 30))

            if self.level_up_available:
                pygame.draw.rect(screen, (147, 208, 207), self.level_up_button)
                level_up_text = FONT_BODY.render("Level Up", True, (249, 249, 242))
                screen.blit(level_up_text, (self.level_up_button.x + 50, self.level_up_button.y + 10))
        
        self.main_menu.achievements.draw_popup(screen)
