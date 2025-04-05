import pygame
import json
from buildings import Base
from units import Player_PeasantUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit
from game_logic import Game
from showroom import Showroom
from achievements import Achievements

class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.active = True
        self.secured_seeds, self.max_level, self.unit_upgrades, self.base_upgrades = self.load_player_data()
        self.achievements = Achievements()
        
        try:
            self.background = pygame.image.load("assets/backgrounds/menu_background.png").convert()
            self.background = pygame.transform.scale(self.background, (1920, 1080))
        except Exception as e:
            print(f"Failed to load menu background: {e}")
            self.background = pygame.Surface((1920, 1080))
            self.background.fill((14, 39, 59))
        
        self.menu_buttons = {
            "Select Level": pygame.Rect(1920 // 2 - 200, 300, 400, 80),
            "Upgrades": pygame.Rect(1920 // 2 - 200, 400, 400, 80),
            "Achievements": pygame.Rect(1920 // 2 - 200, 500, 400, 80),
            "Showroom": pygame.Rect(1920 // 2 - 200, 600, 400, 80),
            "Options": pygame.Rect(1920 // 2 - 200, 700, 400, 80),
            "Exit": pygame.Rect(1920 // 2 - 200, 800, 400, 80)
        }
        self.show_upgrades = False
        self.show_achievements = False
        self.show_levels = False
        self.show_options = False
        self.categories = ["Base", "Units"]
        self.current_category = "Base"
        total_width = len(self.categories) * 150 - 10
        start_x = (1920 - total_width) // 2
        self.category_buttons = {
            "Base": pygame.Rect(start_x, 50, 140, 70),
            "Units": pygame.Rect(start_x + 150, 50, 140, 70)
        }
        self.options_buttons = {
            "Toggle Fullscreen": pygame.Rect(1920 // 2 - 200, 300, 400, 80),
            "Back": pygame.Rect(1920 // 2 - 200, 400, 400, 80)
        }
        self.back_button = pygame.Rect(1920 - 250, 1080 - 120, 200, 80)
        
        default_upgrades = {
            "Peasant": {
                "Health": {"cost": 10, "increase": 3.75, "level": 0},
                "Damage": {"cost": 10, "increase": 1.5, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.075, "level": 0}
            },
            "Archer": {
                "Health": {"cost": 10, "increase": 2.25, "level": 0},
                "Damage": {"cost": 10, "increase": 1.125, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.105, "level": 0}
            },
            "Warrior": {
                "Health": {"cost": 10, "increase": 6.0, "level": 0},
                "Damage": {"cost": 10, "increase": 1.875, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.08625, "level": 0}
            },
            "Tank": {
                "Health": {"cost": 10, "increase": 11.25, "level": 0},
                "Damage": {"cost": 10, "increase": 0.75, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.0375, "level": 0}
            }
        }
        if self.unit_upgrades is None:
            self.unit_upgrades = default_upgrades
        else:
            for unit in default_upgrades:
                if unit not in self.unit_upgrades:
                    self.unit_upgrades[unit] = default_upgrades[unit]
                else:
                    for stat in default_upgrades[unit]:
                        if stat not in self.unit_upgrades[unit]:
                            self.unit_upgrades[unit][stat] = default_upgrades[unit][stat]
        
        self.base_upgrades = self.base_upgrades or {
            "HP": {"cost": 50, "increase": 75, "level": 0},
            "Passive Income": {"cost": 50, "increase": 0.05, "level": 0}
        }

        self.all_unit_types = [Player_PeasantUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit]
        self.unit_types = [Player_PeasantUnit, Player_WarriorUnit, Player_TankUnit]
        if self.max_level >= 5:
            self.unit_types = self.all_unit_types.copy()
            self.achievements.check_achievements("unit_unlocked", {"unit": "Archer"})
        
        self.selected_unit_type = Player_PeasantUnit
        self.unit_buttons = {}
        button_width = 150
        total_unit_width = len(self.unit_types) * (button_width + 30) - 30
        unit_start_x = (1920 - total_unit_width) // 2
        for i, unit_type in enumerate(self.unit_types):
            unit = unit_type("Player", 0)
            sprite = unit.get_icon()
            scaled_sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * 3), int(sprite.get_height() * 3)))
            rect = pygame.Rect(unit_start_x + i * (button_width + 30), 120, button_width, 150)
            sprite_x = rect.x + (rect.width - scaled_sprite.get_width()) // 2
            sprite_y = rect.y + (rect.height - scaled_sprite.get_height()) // 2
            self.unit_buttons[unit_type] = {"rect": rect, "sprite": scaled_sprite, "sprite_pos": (sprite_x, sprite_y)}
        
        self.current_section = 0
        self.level_buttons = {}
        for level in range(1, 21):
            section = (level - 1) // 5
            offset = (level - 1) % 5
            self.level_buttons[level] = pygame.Rect(1920 // 2 - 150, 200 + offset * 90, 300, 80)
        self.prev_button = pygame.Rect(1920 // 2 - 300, 1080 - 180, 150, 80)
        self.next_button = pygame.Rect(1920 // 2 + 150, 1080 - 180, 150, 80)
        
        self.scale_factor = 1.0
        try:
            self.click_sound = pygame.mixer.Sound("C:/Pygame/EvolutionWar/assets/sounds/UI/button_click.wav")
            self.back_sound = pygame.mixer.Sound("C:/Pygame/EvolutionWar/assets/sounds/UI/button_back.wav")
            self.button_bg = pygame.image.load("C:/Pygame/EvolutionWar/assets/ui/ui_buttons.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load menu assets: {e}")
            self.click_sound = None
            self.back_sound = None
            self.button_bg = pygame.Surface((100, 30))
            self.button_bg.fill((147, 208, 207))

    def load_player_data(self):
        try:
            with open("player_data.json", "r") as f:
                data = json.load(f)
                return (
                    data.get("secured_seeds", 100),
                    data.get("max_level", 1),
                    data.get("unit_upgrades", None),
                    data.get("base_upgrades", None)
                )
        except:
            return 100, 1, None, None

    def save_player_data(self):
        data = {
            "secured_seeds": self.secured_seeds,
            "max_level": self.max_level,
            "unit_upgrades": self.unit_upgrades,
            "base_upgrades": self.base_upgrades
        }
        with open("player_data.json", "w") as f:
            json.dump(data, f)

    def get_available_units(self):
        return self.unit_types

    def update(self):
        pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            if not self.show_upgrades and not self.show_levels and not self.show_achievements and not self.show_options:
                for button, rect in self.menu_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        if self.click_sound:
                            self.click_sound.play()
                        if button == "Select Level":
                            self.show_levels = True
                        elif button == "Upgrades":
                            self.show_upgrades = True
                        elif button == "Achievements":
                            self.show_achievements = True
                        elif button == "Showroom":
                            showroom = Showroom(self.screen, self.clock)
                            result = showroom.run()
                            if result == "exit":
                                return "exit"
                        elif button == "Options":
                            self.show_options = True
                        elif button == "Exit":
                            return "exit"
                        return None
            
            elif self.show_options:
                for button, rect in self.options_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        sound = self.back_sound if button == "Back" else self.click_sound
                        if sound:
                            sound.play()
                        if button == "Toggle Fullscreen":
                            self.toggle_fullscreen()
                        elif button == "Back":
                            self.show_options = False
                        return None
            
            elif self.show_upgrades:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_upgrades = False
                    return None
                for category, rect in self.category_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        if self.click_sound:
                            self.click_sound.play()
                        self.current_category = category
                        return None
                
                if self.current_category == "Base":
                    start_y = 1080 // 2 - (len(self.base_upgrades) * 90) // 2
                    for i, (upgrade, data) in enumerate(self.base_upgrades.items()):
                        rect = pygame.Rect(1920 // 2 - 150, start_y + i * 90, 300, 80)
                        if rect.collidepoint(mouse_x, mouse_y) and self.secured_seeds >= data["cost"] and data["level"] < 20:
                            if self.click_sound:
                                self.click_sound.play()
                            self.secured_seeds -= data["cost"]
                            data["level"] += 1
                            self.apply_base_upgrade(upgrade)
                            self.save_player_data()
                            self.achievements.check_achievements("upgrade_applied", {"upgrade_type": upgrade})
                            return None
                
                elif self.current_category == "Units":
                    for unit_type, button in self.unit_buttons.items():
                        if button["rect"].collidepoint(mouse_x, mouse_y):
                            if self.click_sound:
                                self.click_sound.play()
                            self.selected_unit_type = unit_type
                            return None
                    unit_name = self.selected_unit_type.__name__.replace("Player_", "").replace("Unit", "")
                    start_y = 1080 // 2 - (len(self.unit_upgrades[unit_name]) * 90) // 2
                    for i, (upgrade, data) in enumerate(self.unit_upgrades[unit_name].items()):
                        rect = pygame.Rect(1920 // 2 - 150, start_y + i * 90, 300, 80)
                        if rect.collidepoint(mouse_x, mouse_y) and self.secured_seeds >= data["cost"] and data["level"] < 20:
                            if self.click_sound:
                                self.click_sound.play()
                            self.secured_seeds -= data["cost"]
                            data["level"] += 1
                            self.save_player_data()
                            self.achievements.check_achievements("upgrade_applied", {"upgrade_type": upgrade})
                            return upgrade.lower()
            
            elif self.show_levels:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_levels = False
                    return None
                if self.prev_button.collidepoint(mouse_x, mouse_y) and self.current_section > 0:
                    if self.click_sound:
                        self.click_sound.play()
                    self.current_section -= 1
                    return None
                if self.next_button.collidepoint(mouse_x, mouse_y) and self.current_section < 3:
                    section_start = self.current_section * 5 + 1
                    section_end = min(section_start + 4, 20)
                    if self.max_level >= section_end:
                        if self.click_sound:
                            self.click_sound.play()
                        self.current_section += 1
                    return None
                for level, rect in self.level_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y) and level <= self.max_level:
                        if self.click_sound:
                            self.click_sound.play()
                        section_start = self.current_section * 5 + 1
                        section_end = section_start + 4
                        if section_start <= level <= section_end:
                            self.active = False
                            return level
                return None
            
            elif self.show_achievements:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_achievements = False
                    return None
        
        return None

    def toggle_fullscreen(self):
        current_flags = self.screen.get_flags()
        if current_flags & pygame.FULLSCREEN:
            self.screen = pygame.display.set_mode((1920, 1080))
            self.scale_factor = 1.0
            self.background = pygame.transform.scale(self.background, (1920, 1080))
        else:
            screen_info = pygame.display.Info()
            self.screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h), pygame.FULLSCREEN)
            self.scale_factor = screen_info.current_w / 1920
            self.background = pygame.transform.smoothscale(self.background, (screen_info.current_w, screen_info.current_h))
        for rect in self.menu_buttons.values():
            rect.x = int(rect.x * self.scale_factor)
            rect.y = int(rect.y * self.scale_factor)
            rect.width = int(rect.width * self.scale_factor)
            rect.height = int(rect.height * self.scale_factor)

    def apply_base_upgrade(self, upgrade):
        if upgrade == "HP":
            Base.base_health += self.base_upgrades["HP"]["increase"]
        elif upgrade == "Passive Income":
            Game.passive_income += self.base_upgrades["Passive Income"]["increase"]

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        
        # Use TrueType fonts with increased size for clarity
        try:
            FONT_CTA = pygame.font.Font("C:/Pygame/EvolutionWar/assets/fonts/OpenSans-Bold.ttf", 40)
            FONT_BODY = pygame.font.Font("C:/Pygame/EvolutionWar/assets/fonts/OpenSans-Regular.ttf", 32)
        except Exception as e:
            print(f"Failed to load fonts in MainMenu: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 40, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 32)
        
        if not self.show_upgrades and not self.show_levels and not self.show_achievements and not self.show_options:
            title_text = FONT_CTA.render("Evolution War", True, (249, 249, 242))
            screen.blit(title_text, (1920 // 2 - title_text.get_width() // 2, 200))
            for button, rect in self.menu_buttons.items():
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                screen.blit(bg, (rect.x, rect.y))
                text = FONT_CTA.render(button, True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
        
        elif self.show_options:
            for button, rect in self.options_buttons.items():
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                screen.blit(bg, (rect.x, rect.y))
                text = FONT_CTA.render(button, True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
        
        elif self.show_upgrades:
            for category, rect in self.category_buttons.items():
                color = (128, 131, 134) if category != self.current_category else (147, 208, 207)
                pygame.draw.rect(screen, color, rect)
                text = FONT_BODY.render(category, True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            if self.current_category == "Base":
                start_y = 1080 // 2 - (len(self.base_upgrades) * 90) // 2
                for i, (upgrade, data) in enumerate(self.base_upgrades.items()):
                    rect = pygame.Rect(1920 // 2 - 150, start_y + i * 90, 300, 80)
                    bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                    if self.secured_seeds >= data["cost"]:
                        screen.blit(bg, (rect.x, rect.y))
                    else:
                        greyed = bg.copy()
                        greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                        screen.blit(greyed, (rect.x, rect.y))
                    text = FONT_BODY.render(f"{upgrade} (Lv {data['level']}) - {data['cost']} Seeds", True, (249, 249, 242))
                    screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            elif self.current_category == "Units":
                for unit_type, button in self.unit_buttons.items():
                    screen.blit(button["sprite"], button["sprite_pos"])
                    if unit_type == self.selected_unit_type:
                        pygame.draw.rect(screen, (147, 208, 207), button["rect"], 2)
                unit_name = self.selected_unit_type.__name__.replace("Player_", "").replace("Unit", "")
                start_y = 1080 // 2 - (len(self.unit_upgrades[unit_name]) * 90) // 2
                for i, (upgrade, data) in enumerate(self.unit_upgrades[unit_name].items()):
                    rect = pygame.Rect(1920 // 2 - 150, start_y + i * 90, 300, 80)
                    bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                    if self.secured_seeds >= data["cost"]:
                        screen.blit(bg, (rect.x, rect.y))
                    else:
                        greyed = bg.copy()
                        greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                        screen.blit(greyed, (rect.x, rect.y))
                    text = FONT_BODY.render(f"{upgrade} (Lv {data['level']}) - {data['cost']} Seeds", True, (249, 249, 242))
                    screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        
        elif self.show_levels:
            level_title = FONT_CTA.render(f"Select Level (Levels {self.current_section * 5 + 1}-{min((self.current_section + 1) * 5, 20)})", True, (249, 249, 242))
            screen.blit(level_title, (1920 // 2 - level_title.get_width() // 2, 100))
            section_start = self.current_section * 5 + 1
            section_end = min(section_start + 4, 20)
            for level in range(section_start, section_end + 1):
                rect = self.level_buttons[level]
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                if level <= self.max_level:
                    screen.blit(bg, (rect.x, rect.y))
                else:
                    greyed = bg.copy()
                    greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                    screen.blit(greyed, (rect.x, rect.y))
                text = FONT_BODY.render(f"Level {level}", True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            bg_prev = pygame.transform.scale(self.button_bg, (self.prev_button.width, self.prev_button.height))
            if self.current_section > 0:
                screen.blit(bg_prev, (self.prev_button.x, self.prev_button.y))
            else:
                greyed = bg_prev.copy()
                greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(greyed, (self.prev_button.x, self.prev_button.y))
            prev_text = FONT_CTA.render("Prev", True, (249, 249, 242))
            screen.blit(prev_text, (self.prev_button.x + (self.prev_button.width - prev_text.get_width()) // 2, self.prev_button.y + (self.prev_button.height - prev_text.get_height()) // 2))
            
            bg_next = pygame.transform.scale(self.button_bg, (self.next_button.width, self.next_button.height))
            if self.current_section < 3 and self.max_level >= section_end:
                screen.blit(bg_next, (self.next_button.x, self.next_button.y))
            else:
                greyed = bg_next.copy()
                greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(greyed, (self.next_button.x, self.next_button.y))
            next_text = FONT_CTA.render("Next", True, (249, 249, 242))
            screen.blit(next_text, (self.next_button.x + (self.next_button.width - next_text.get_width()) // 2, self.next_button.y + (self.next_button.height - next_text.get_height()) // 2))
            
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        
        elif self.show_achievements:
            self.achievements.draw_achievements_menu(screen)
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        
        seeds_text = FONT_BODY.render(f"Secured Seeds: {int(self.secured_seeds)}", True, (249, 249, 242))
        screen.blit(seeds_text, (1920 - seeds_text.get_width() - 20, 50))
        self.achievements.draw_popup(screen)