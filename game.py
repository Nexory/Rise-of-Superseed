import pygame
from menu import MainMenu
from game_logic import Game
from units import preload_all_animations

def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("Evolution War")
    clock = pygame.time.Clock()

    # Load and play background music with infinite loop
    try:
        pygame.mixer.music.load("C:/Pygame/EvolutionWar/assets/sounds/Menu.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # -1 ensures infinite looping
    except Exception as e:
        print(f"Failed to load or play Menu.mp3: {e}")

    preload_all_animations()
    main_menu = MainMenu(screen, clock)
    running = True

    while running:
        if main_menu.active:
            main_menu.update()
            main_menu.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    result = main_menu.handle_event(event)
                    if isinstance(result, int):
                        game = Game(result, main_menu, screen, clock)
                        game.run()
                        main_menu.active = True
                    elif result == "exit":
                        running = False
                elif event.type == pygame.MOUSEWHEEL:
                    main_menu.handle_event(event)
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

        pygame.display.flip()
        clock.tick(60)

    main_menu.save_player_data()
    pygame.quit()

if __name__ == "__main__":
    main()