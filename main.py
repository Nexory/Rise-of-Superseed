import pygame
import asyncio
from menu import MainMenu
from game_logic import Game
from units import preload_all_animations

async def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("Evolution War")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 36)

    screen.fill((255, 0, 0))
    screen.blit(font.render("Initializing...", True, (255, 255, 255)), (50, 50))
    pygame.display.flip()
    await asyncio.sleep(1)

    screen.fill((255, 165, 0))
    screen.blit(font.render("Creating Menu...", True, (255, 255, 255)), (50, 100))
    pygame.display.flip()
    await asyncio.sleep(0.5)
    try:
        main_menu = MainMenu(screen, clock)
    except Exception as e:
        screen.fill((255, 0, 0))
        screen.blit(font.render(f"Menu Creation Failed: {str(e)}", True, (255, 255, 255)), (50, 150))
        pygame.display.flip()
        await asyncio.sleep(5)
        raise

    screen.fill((255, 255, 0))
    screen.blit(font.render("Preloading Animations...", True, (255, 255, 255)), (50, 150))
    pygame.display.flip()
    await asyncio.sleep(0.5)
    preload_all_animations()

    screen.fill((0, 255, 0))
    screen.blit(font.render("Starting Menu Loop...", True, (255, 255, 255)), (50, 200))
    pygame.display.flip()
    await asyncio.sleep(0.5)

    while main_menu.active:
        main_menu.run()
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    if main_menu.game:
        screen.fill((0, 0, 255))
        screen.blit(font.render("Starting Game...", True, (255, 255, 255)), (50, 250))
        pygame.display.flip()
        await asyncio.sleep(0.5)

        screen.blit(font.render("Creating Game Object...", True, (255, 255, 255)), (50, 300))
        pygame.display.flip()
        await asyncio.sleep(0.5)
        try:
            game = Game(main_menu.level_number, main_menu, screen, clock)
        except Exception as e:
            screen.blit(font.render(f"Game Init Failed: {str(e)}", True, (255, 255, 255)), (50, 350))
            pygame.display.flip()
            await asyncio.sleep(5)
            raise

        screen.blit(font.render("Running Game...", True, (255, 255, 255)), (50, 400))
        pygame.display.flip()
        await asyncio.sleep(0.5)
        await game.run()

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())