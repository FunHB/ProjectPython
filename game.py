import pygame
import pygame_gui

import numpy as np

from forest import Forest, Type


class Game:
    def __init__(self, forest: Forest, width: int = 1600, height: int = 900) -> None:
        pygame.init()
        pygame.display.set_caption("Symulacja Pożaru Lasu")

        self.width = width
        self.height = height
        self.window_surface = pygame.display.set_mode((self.width, self.height))
        self.manager = pygame_gui.UIManager((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True

        self.single_block_size = 4
        self.forest = forest

        self.grid_surface = pygame.Surface((forest.size, forest.size))
        self.grid_pixels = np.zeros((forest.size, forest.size, 3), dtype=np.uint8)

    def start(self) -> None:
        while self.running:
            time_delta = self.clock.tick(self.fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                self.manager.process_events(event)

            self.manager.update(time_delta)

            # Aktualizacja stanu lasu
            self.forest.next_gen(pygame.time.get_ticks())

            # Aktualizacja kolorów pikseli
            color_array = self.get_color_array()
            pygame.surfarray.blit_array(self.grid_surface, color_array)
            scaled_size = (self.forest.size * self.single_block_size, self.forest.size * self.single_block_size)
            scaled_grid = pygame.transform.scale(self.grid_surface, scaled_size)

            # Renderowanie GUI
            self.window_surface.fill((24, 24, 24))
            self.window_surface.blit(scaled_grid, (400, 50))
            self.manager.draw_ui(self.window_surface)

            pygame.display.flip()

    def get_color_array(self) -> np.ndarray:
        grid_flat = self.forest.grid.flatten()
        humidity_flat = self.forest.humidity.flatten()

        colors = np.zeros((self.forest.size ** 2, 3), dtype=np.uint8)

        # Type.EMPTY
        colors[grid_flat == Type.EMPTY] = [220, 220, 220]

        # Type.TREE
        green_intensity = np.clip((120 / humidity_flat[grid_flat == Type.TREE]).astype(np.uint8), 0, 255)
        colors[grid_flat == Type.TREE] = np.stack([np.zeros_like(green_intensity),
                                                   green_intensity,
                                                   np.zeros_like(green_intensity)], axis=1)

        # Type.BURNING
        colors[grid_flat == Type.BURNING] = [220, 0, 0]

        # Type.LIGHTNING
        colors[grid_flat == Type.LIGHTNING] = [100, 100, 220]

        # Type.ASH
        colors[grid_flat == Type.ASH] = [50, 50, 50]

        return colors.reshape((self.forest.size, self.forest.size, 3))
