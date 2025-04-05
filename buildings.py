# buildings.py
import pygame

class Base:
    base_health = 1000

    def __init__(self, x, y, health, sprite_path, is_player):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = health
        self.sprite_path = sprite_path
        self.is_player = is_player
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            orig_width, orig_height = self.sprite.get_size()
            new_width = int(orig_width * 0.75)
            new_height = int(orig_height * 0.75)
            self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
            if not is_player:
                self.sprite = pygame.transform.flip(self.sprite, True, False)
        except Exception as e:
            print(f"Failed to load base sprite {sprite_path}: {e}")
            self.sprite = pygame.Surface((225, 300))
            self.sprite.fill((0, 255, 0) if is_player else (255, 0, 0))

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.sprite.get_width(), self.sprite.get_height())

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        bar_width = self.sprite.get_width() - 10
        bar_height = 10
        health_ratio = self.health / self.max_health
        fill_width = bar_width * health_ratio
        bar_x = self.x + 5
        bar_y = self.y - 20
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        fill_color = (0, 255, 0) if self.is_player else (255, 0, 0)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        hp_font = pygame.font.SysFont("Arial", 16)
        hp_text = hp_font.render(f"{int(self.health)}/{self.max_health}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + (bar_width - hp_text.get_width()) // 2, bar_y - 20))