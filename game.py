import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from forest import Forest, Type


class Game:
    def __init__(self, forest: Forest) -> None:
        pygame.init()

        self.fps = 10
        self.block_size = 800 // forest.size

        self.size = self.block_size * forest.size
        self.screen = pygame.display.set_mode((self.size + 200, self.size))
        self.clock = pygame.time.Clock()
        self.running = True
        self.forest = forest

        self.manager = pygame_gui.UIManager((self.size + 200, self.size))
        self.restart_button = UIButton(
            relative_rect=pygame.Rect((self.size + 25, (self.size - 150) // 2), (150, 50)),
            text='Restart',
            manager=self.manager
        )

    def start(self) -> None:
        while self.running:
            time_delta = self.clock.tick(self.fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.restart_button:
                        self.forest.simulation_reset()

                self.manager.process_events(event)

            self.manager.update(time_delta)

            self.screen.fill((24, 24, 24))

            # Game Render
            self.draw_grid()
            self.forest.next_gen(pygame.time.get_ticks())

            # Renderowanie GUI
            self.manager.draw_ui(self.screen)

            pygame.display.flip()

    def draw_grid(self) -> None:
        for x in range(0, self.forest.size):
            for y in range(0, self.forest.size):
                rect = pygame.Rect(x * self.block_size, y * self.block_size, self.block_size, self.block_size)
                pos = (x, y)
                pygame.draw.rect(self.screen, self.get_color(pos), rect)

    def get_color(self, pos: tuple[int, int]) -> tuple[int, int, int]:
        cell_type = self.forest.grid[pos]
        humidity = self.forest.humidity[pos]

        if cell_type == Type.LIGHTNING:
            return 100, 100, 220

        if cell_type == Type.BURNING:
            return 220, 0, 0

        if cell_type == Type.ASH:
            return 50, 50, 50

        if cell_type == Type.TREE:
            green_intensity = int(120 / humidity)
            return 0, max(0, green_intensity), 0

        return 220, 220, 220
