import pygame
from units import Player_ArcherUnit, Bandit_Razor

class EventHandler:
    def __init__(self, game):
        self.game = game
        self.okay_button = pygame.Rect(0, 0, 250, 80)
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/UI/button_click.wav")
            self.text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
            self.button_bg = pygame.image.load("assets/ui/ui_buttons.png").convert_alpha()
        except Exception:
            self.click_sound = None
            self.text_bg = pygame.Surface((100, 30))
            self.text_bg.fill((50, 50, 50))
            self.button_bg = pygame.Surface((100, 30))
            self.button_bg.fill((147, 208, 207))

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if self.okay_button.collidepoint(mouse_x, mouse_y):
                if self.click_sound:
                    self.click_sound.play()
                if self.game.show_intro:
                    self.game.show_intro = False
                elif self.game.show_end_story:
                    self.game.show_end_story = False
                    self.game.handle_level_completion()
                elif self.game.show_bandit_intro:
                    self.game.show_bandit_intro = False
                elif self.game.show_king_threat:
                    self.game.show_king_threat = False
                elif self.game.show_surrender_part_two:
                    self.game.show_surrender_part_two = False
                    self.game.show_end_story = True

    def update(self):
        if self.game.show_bandit_surrender:
            razor_unit = next((unit for unit in self.game.enemy_units if isinstance(unit, Bandit_Razor)), None)
            if self.game.cart and razor_unit and self.game.bandit_king:
                razor_dist = abs(razor_unit.x - self.game.bandit_king.x)
                if razor_dist < 180:
                    self.game.cart.moving = False
                    self.game.show_bandit_surrender = False
                    self.game.show_surrender_part_two = True

    def handle_units_moving_back(self):
        if self.game.units_moving_back:
            all_done = True
            front_unit = max(self.game.units, key=lambda u: u.x if u.state != "die" else -float('inf'), default=None)
            if front_unit:
                FRONT_TARGET_X = 768
                unit_width = 120
                for i, unit in enumerate(sorted(self.game.units, key=lambda u: u.x, reverse=True)):
                    if unit.state != "die":
                        unit.state = "run"
                        unit.is_retreating = True
                        original_speed = unit.speed
                        unit.speed = 1.5
                        target_x = max(100, FRONT_TARGET_X - i * unit_width)
                        if unit.x > target_x:
                            unit.x -= unit.speed * 2
                            unit.update_animation()
                            all_done = False
                        else:
                            unit.x = target_x
                            unit.state = "idle"
                            unit.is_retreating = False
                            unit.speed = original_speed
            if all_done:
                self.game.units_moving_back = False
            return True
        return False

    def handle_king_moving(self):
        if self.game.king_moving and self.game.bandit_king:
            self.game.bandit_king.state = "run"
            self.game.bandit_king.direction = -1
            KING_TARGET_X = 1152
            if self.game.bandit_king.x > KING_TARGET_X:
                self.game.bandit_king.x -= self.game.bandit_king.speed
                self.game.bandit_king.update_animation()
            else:
                self.game.bandit_king.x = KING_TARGET_X
                self.game.bandit_king.state = "idle"
                self.game.king_moving = False
                self.game.show_king_threat = True
            return True
        return False

    def draw(self, screen):
        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 40)
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 32)
        except Exception:
            FONT_CTA = pygame.font.SysFont("Open Sans", 40, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 32)
        PADDING = 40

        if self.game.show_intro:
            overlay = pygame.Surface((1920, 1040))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))
            story_text = [
                "The zombies have risen from the graves!",
                "Defend your base with your trusty peasants.",
                "Good luck, commander!"
            ]
            text_surfaces = [FONT_BODY.render(line, True, (249, 249, 242)) for line in story_text]
            max_width = max(surface.get_width() for surface in text_surfaces) + 2 * PADDING
            total_height = sum(surface.get_height() for surface in text_surfaces) + 2 * PADDING
            bg = pygame.transform.scale(self.text_bg, (max_width, total_height))
            bg_x = 1920 // 2 - max_width // 2
            bg_y = 880 // 2 - total_height // 2
            screen.blit(bg, (bg_x, bg_y))
            for i, surface in enumerate(text_surfaces):
                screen.blit(surface, (bg_x + PADDING + (max_width - 2 * PADDING - surface.get_width()) // 2, bg_y + PADDING + i * surface.get_height()))
            self.okay_button.topleft = (1920 // 2 - 125, bg_y + total_height + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))

        elif self.game.show_end_story:
            overlay = pygame.Surface((1920, 1040))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))
            story_text = [
                "The bandit threat is subdued!",
                "A new ally joins your ranks."
            ]
            text_surfaces = [FONT_BODY.render(line, True, (249, 249, 242)) for line in story_text]
            unlock_text = FONT_BODY.render("New Unit Unlocked: Archer", True, (249, 249, 242))
            max_width = max(max(surface.get_width() for surface in text_surfaces), unlock_text.get_width()) + 2 * PADDING
            total_height = sum(surface.get_height() for surface in text_surfaces) + unlock_text.get_height() + 192 + 20 + 2 * PADDING
            bg = pygame.transform.scale(self.text_bg, (max_width, total_height))
            bg_x = 1920 // 2 - max_width // 2
            bg_y = 880 // 2 - total_height // 2
            screen.blit(bg, (bg_x, bg_y))
            for i, surface in enumerate(text_surfaces):
                screen.blit(surface, (bg_x + PADDING + (max_width - 2 * PADDING - surface.get_width()) // 2, bg_y + PADDING + i * surface.get_height()))
            try:
                archer = Player_ArcherUnit("Player", 0)
                archer_icon = pygame.transform.scale(archer.animations["idle"][0], (192, 192))
                screen.blit(archer_icon, (bg_x + (max_width - 192) // 2, bg_y + PADDING + sum(surface.get_height() for surface in text_surfaces)))
            except Exception:
                pass  # Skip icon if it fails
            screen.blit(unlock_text, (bg_x + PADDING + (max_width - 2 * PADDING - unlock_text.get_width()) // 2, bg_y + PADDING + sum(surface.get_height() for surface in text_surfaces) + 192 + 20))
            self.okay_button.topleft = (1920 // 2 - 125, bg_y + total_height + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))

        elif self.game.show_bandit_intro and self.game.bandit_king:
            text = FONT_BODY.render("Who dares trespass?", True, (249, 249, 242))
            bg = pygame.transform.scale(self.text_bg, (text.get_width() + 2 * PADDING, text.get_height() + 2 * PADDING))
            bg_x = self.game.bandit_king.x - (text.get_width() + 2 * PADDING) // 2
            bg_y = self.game.bandit_king.y - 120
            screen.blit(bg, (bg_x, bg_y))
            screen.blit(text, (bg_x + PADDING, bg_y + PADDING))
            self.okay_button.topleft = (bg_x + (bg.get_width() - self.okay_button.width) // 2, bg_y + bg.get_height() + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))

        elif self.game.show_king_threat and self.game.bandit_king:
            text = FONT_BODY.render("Prepare to face my wrath!", True, (249, 249, 242))
            bg = pygame.transform.scale(self.text_bg, (text.get_width() + 2 * PADDING, text.get_height() + 2 * PADDING))
            bg_x = self.game.bandit_king.x - (text.get_width() + 2 * PADDING) // 2
            bg_y = self.game.bandit_king.y - 120
            screen.blit(bg, (bg_x, bg_y))
            screen.blit(text, (bg_x + PADDING, bg_y + PADDING))
            self.okay_button.topleft = (bg_x + (bg.get_width() - self.okay_button.width) // 2, bg_y + bg.get_height() + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))

        elif self.game.show_bandit_surrender and self.game.bandit_king:
            lines = [
                "Cease fire! Greater foes loom",
                "ahead—we must unite."
            ]
            text_surfaces = [FONT_BODY.render(line, True, (249, 249, 242)) for line in lines]
            max_width = max(surface.get_width() for surface in text_surfaces) + 2 * PADDING
            total_height = sum(surface.get_height() for surface in text_surfaces) + 2 * PADDING
            bg = pygame.transform.scale(self.text_bg, (max_width, total_height))
            bg_x = self.game.bandit_king.x - max_width // 2
            bg_y = self.game.bandit_king.y - 140
            screen.blit(bg, (bg_x, bg_y))
            for i, surface in enumerate(text_surfaces):
                screen.blit(surface, (bg_x + PADDING + (max_width - 2 * PADDING - surface.get_width()) // 2, bg_y + PADDING + i * surface.get_height()))

        elif self.game.show_surrender_part_two and self.game.bandit_king:
            lines = [
                "Take these bows and arrows;",
                "they’ll serve you well."
            ]
            text_surfaces = [FONT_BODY.render(line, True, (249, 249, 242)) for line in lines]
            max_width = max(surface.get_width() for surface in text_surfaces) + 2 * PADDING
            total_height = sum(surface.get_height() for surface in text_surfaces) + 2 * PADDING
            bg = pygame.transform.scale(self.text_bg, (max_width, total_height))
            bg_x = self.game.bandit_king.x - max_width // 2
            bg_y = self.game.bandit_king.y - 140
            screen.blit(bg, (bg_x, bg_y))
            for i, surface in enumerate(text_surfaces):
                screen.blit(surface, (bg_x + PADDING + (max_width - 2 * PADDING - surface.get_width()) // 2, bg_y + PADDING + i * surface.get_height()))
            self.okay_button.topleft = (bg_x + (max_width - self.okay_button.width) // 2, bg_y + total_height + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))