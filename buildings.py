# Version 2.5
import pygame

class Base:
    base_health = 1000

    def __init__(self, x, y, health, sprite_path, is_player):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.is_player = is_player
        self.sprite_path = sprite_path
        self.destroyed = False
        self.load_sprites()

    def load_sprites(self):
        try:
            self.sprite = pygame.image.load(self.sprite_path).convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (150, 300))
            if self.is_player and "base" in self.sprite_path.lower():
                self.sprite = pygame.transform.flip(self.sprite, True, False)
            if self.is_player:
                destroyed_path = ("assets/buildings/Player/Skin 1/player_base_destroyed.png" 
                                 if "base" in self.sprite_path.lower() 
                                 else "assets/buildings/Player/Skin 1/player_tower_destroyed.png")
                self.destroyed_sprite = pygame.image.load(destroyed_path).convert_alpha()
                self.destroyed_sprite = pygame.transform.scale(self.destroyed_sprite, (150, 300))
                if "base" in self.sprite_path.lower():
                    self.destroyed_sprite = pygame.transform.flip(self.destroyed_sprite, True, False)
            else:
                self.destroyed_sprite = self.sprite
        except Exception as e:
            print(f"Failed to load sprite: {e}")
            self.sprite = pygame.Surface((150, 300))
            self.sprite.fill((0, 0, 255) if self.is_player else (255, 0, 0))
            self.destroyed_sprite = self.sprite.copy()

    def get_rect(self):
        return pygame.Rect(self.x + 25, self.y, 100, 300)  # Kept at 100px width for bases

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.destroyed = True

    def draw(self, screen):
        screen.blit(self.destroyed_sprite if self.destroyed else self.sprite, (self.x, self.y))
        if not (self.is_player and "tower" in self.sprite_path.lower()):
            bar_width = 144
            bar_height = 12
            health_ratio = self.health / self.max_health
            fill_width = bar_width * health_ratio
            bar_x = self.x + (150 - bar_width) // 2
            bar_y = self.y - 22
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            fill_color = (0, 255, 0) if self.is_player else (255, 0, 0)
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))