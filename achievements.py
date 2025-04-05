import pygame
import json

class Achievements:
    def __init__(self):
        self.achievements = {
            "Beat Level 1": {"description": "Complete Level 1", "unlocked": False},
            "Beat Level 5": {"description": "Complete Level 5", "unlocked": False},
            "Unlock Archer": {"description": "Unlock the Archer unit", "unlocked": False},
            "Secure 1000 Seeds": {"description": "Accumulate 1000 secured seeds", "unlocked": False},
            "Kill 5 Units": {"description": "Kill 5 enemy units", "unlocked": False},
            "Kill 50 Units": {"description": "Kill 50 enemy units", "unlocked": False},
            "Upgrade Base HP": {"description": "Upgrade your base's HP", "unlocked": False},
            "Upgrade Unit Health": {"description": "Upgrade a unit's health", "unlocked": False},
            "Spawn 10 Units": {"description": "Spawn 10 units in a single game", "unlocked": False},
            "Win Without Losing Health": {"description": "Win a level without your base losing health", "unlocked": False},
            "Kill a Tank": {"description": "Kill an enemy Tank unit", "unlocked": False},
            "Survive 5 Minutes": {"description": "Survive for 5 minutes in a level", "unlocked": False},
            "Collect 100 Seeds": {"description": "Collect 100 seeds in a single game", "unlocked": False},
            "Unlock All Units": {"description": "Unlock all player units", "unlocked": False},
            "Max Upgrade a Unit": {"description": "Fully upgrade a unit's stats", "unlocked": False},
            "Destroy Enemy Base": {"description": "Destroy the enemy base in under 10 minutes", "unlocked": False},
            "Kill with Archer": {"description": "Kill an enemy with an Archer unit", "unlocked": False},
            "Spawn a Tank": {"description": "Spawn a Tank unit", "unlocked": False},
            "Upgrade Passive Income": {"description": "Upgrade your passive income", "unlocked": False},
            "Win 3 Levels": {"description": "Win 3 different levels", "unlocked": False}
        }
        self.load_achievements()
        self.popup_queue = []
        self.popup_duration = 3000
        self.popup_start_time = 0
        self.kill_count = 0
        self.level_wins = 0
        self.units_spawned = 0
        self.game_start_time = 0
        self.seeds_collected = 0
        self.base_health_lost = False

    def load_achievements(self):
        try:
            import js  # Pygbag provides this for JavaScript interop
            data = js.loadPlayerData()
            if not data or not isinstance(data, dict):
                print("Empty or invalid achievements data from localStorage")
                return
            for key in self.achievements:
                if key in data:
                    if isinstance(data[key], dict) and "unlocked" in data[key]:
                        self.achievements[key]["unlocked"] = data[key]["unlocked"]
                    elif isinstance(data[key], bool):
                        self.achievements[key]["unlocked"] = data[key]
        except Exception as e:
            print(f"Failed to load achievements from localStorage: {e}")

    def save_achievements(self):
        data = {key: {"unlocked": value["unlocked"]} for key, value in self.achievements.items()}
        try:
            import js
            js.savePlayerData(data)
        except Exception as e:
            print(f"Failed to save achievements to localStorage: {e}")

    def unlock_achievement(self, achievement):
        if achievement in self.achievements and not self.achievements[achievement]["unlocked"]:
            self.achievements[achievement]["unlocked"] = True
            self.popup_queue.append(achievement)
            if len(self.popup_queue) == 1:
                self.popup_start_time = pygame.time.get_ticks()
            self.save_achievements()

    def check_achievements(self, event, data):
        if event == "level_complete":
            level = data["level"]
            if level == 1:
                self.unlock_achievement("Beat Level 1")
            elif level == 5:
                self.unlock_achievement("Beat Level 5")
            self.level_wins += 1
            if self.level_wins >= 3:
                self.unlock_achievement("Win 3 Levels")
            if not self.base_health_lost:
                self.unlock_achievement("Win Without Losing Health")
            if pygame.time.get_ticks() - self.game_start_time < 600000:
                self.unlock_achievement("Destroy Enemy Base")
        elif event == "unit_killed":
            self.kill_count += 1
            if self.kill_count >= 5:
                self.unlock_achievement("Kill 5 Units")
            if self.kill_count >= 50:
                self.unlock_achievement("Kill 50 Units")
            if data["unit"].name == "Zombie_Tank":
                self.unlock_achievement("Kill a Tank")
            if data.get("killer") == "Player_Archer":
                self.unlock_achievement("Kill with Archer")
        elif event == "unit_spawned":
            self.units_spawned += 1
            if self.units_spawned >= 10:
                self.unlock_achievement("Spawn 10 Units")
            if data["unit"].name == "Player_Tank":
                self.unlock_achievement("Spawn a Tank")
        elif event == "game_started":
            self.game_start_time = pygame.time.get_ticks()
            self.units_spawned = 0
            self.seeds_collected = 0
            self.base_health_lost = False
        elif event == "seeds_collected":
            self.seeds_collected += data["seeds"]
            if self.seeds_collected >= 100:
                self.unlock_achievement("Collect 100 Seeds")
        elif event == "upgrade_applied":
            upgrade_type = data["upgrade_type"]
            if upgrade_type == "HP":
                self.unlock_achievement("Upgrade Base HP")
            elif upgrade_type in ["Health", "Damage", "Attack Speed", "Movement Speed"]:
                self.unlock_achievement("Upgrade Unit Health")
            elif upgrade_type == "Passive Income":
                self.unlock_achievement("Upgrade Passive Income")
        elif event == "base_damaged":
            self.base_health_lost = True

    def update(self):
        if pygame.time.get_ticks() - self.game_start_time >= 300000:
            self.unlock_achievement("Survive 5 Minutes")

    def draw_popup(self, screen):
        if self.popup_queue:
            now = pygame.time.get_ticks()
            if now - self.popup_start_time > self.popup_duration:
                self.popup_queue.pop(0)
                if self.popup_queue:
                    self.popup_start_time = now
            if self.popup_queue:
                achievement = self.popup_queue[0]
                text = f"Achievement Unlocked: {achievement}"
                font = pygame.font.SysFont("Arial", 36, bold=True)
                text_surface = font.render(text, True, (255, 255, 255))
                screen_width, screen_height = screen.get_size()
                popup_width = text_surface.get_width() + 40
                popup_height = text_surface.get_height() + 40
                popup_x = (screen_width - popup_width) // 2
                popup_y = (screen_height - popup_height) // 2
                pygame.draw.rect(screen, (50, 50, 50), (popup_x, popup_y, popup_width, popup_height))
                screen.blit(text_surface, (popup_x + 20, popup_y + 20))

    def draw_achievements_menu(self, screen):
        screen.blit(pygame.Surface((1920, 1080)), (0, 0))
        font = pygame.font.SysFont("Arial", 24)
        y = 50
        for name, data in self.achievements.items():
            color = (0, 255, 0) if data["unlocked"] else (255, 0, 0)
            text = font.render(f"{name}: {data['description']} - {'Unlocked' if data['unlocked'] else 'Locked'}", True, color)
            screen.blit(text, (50, y))
            y += 30