# showroom.py
import pygame

class Showroom:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.active = True
        self.sprite_data = {}
        self.load_sprites()
        self.back_button = pygame.Rect(1920 - 200, 1080 - 100, 150, 50)
        self.scroll_y = 0
        self.max_scroll = max(0, (len(self.sprite_data) // 5 + 1) * 200 - 1080)
        self.frame_delay = 100

    def load_sprites(self):
        # Hardcode sprite paths since os.walk isn't available in browser
        sprite_paths = [
            "assets/sprites/Player/Player_Peasant.png",
            "assets/sprites/Player/Player_Archer.png",
            "assets/sprites/Player/Player_Warrior.png",
            "assets/sprites/Player/Player_Tank.png",
            "assets/sprites/Bandits/Bandit_Razor.png",
            # Add more as needed
        ]
        for path in sprite_paths:
            try:
                spritesheet = pygame.image.load(path).convert_alpha()
                frame_width = 192
                frame_height = 192
                frames_per_state = 14
                if spritesheet.get_width() >= frame_width and spritesheet.get_height() >= frame_height:
                    idle_frames = []
                    for i in range(frames_per_state):
                        x = i * frame_width
                        if x + frame_width <= spritesheet.get_width():
                            frame = spritesheet.subsurface((x, 0, frame_width, frame_height))
                            frame = pygame.transform.scale(frame, (192, 192))
                            idle_frames.append(frame)
                        else:
                            break
                    if idle_frames:
                        name = path.split('/')[-1].replace('.png', '')
                        faction = path.split('/')[-2]
                        full_name = f"{faction}/{name}"
                        self.sprite_data[full_name] = {
                            "frames": idle_frames,
                            "frame": 0,
                            "last_update": pygame.time.get_ticks()
                        }
            except Exception as e:
                print(f"Failed to load {path}: {e}")

    def update_animations(self):
        now = pygame.time.get_ticks()
        for data in self.sprite_data.values():
            if now - data["last_update"] >= self.frame_delay:
                data["frame"] = (data["frame"] + 1) % len(data["frames"])
                data["last_update"] = now

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.collidepoint(event.pos):
                self.active = False
                return "back"
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, min(self.scroll_y - event.y * 50, self.max_scroll))
        return None

    def draw(self, screen):
        screen.fill((14, 39, 59))
        FONT_BODY = pygame.font.SysFont("Open Sans", 24)

        for i, (name, data) in enumerate(self.sprite_data.items()):
            col = i % 5
            row = i // 5
            x = 50 + col * 400
            y = 50 + row * 200 - self.scroll_y
            if 0 <= y <= 1080 - 192:
                frame = data["frames"][data["frame"]]
                screen.blit(frame, (x, y))
                text = FONT_BODY.render(name, True, (249, 249, 242))
                screen.blit(text, (x + (192 - text.get_width()) // 2, y + 192))

        pygame.draw.rect(screen, (147, 208, 207), self.back_button)
        back_text = FONT_BODY.render("Back", True, (249, 249, 242))
        screen.blit(back_text, (self.back_button.x + 10, self.back_button.y + 15))

    def run(self):
        while self.active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                result = self.handle_event(event)
                if result:
                    return result
            self.update_animations()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
        return "back"