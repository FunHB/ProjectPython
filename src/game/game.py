from src.simulation.forest import Forest, Type
from .ui_components import LeftPanel, HumidityRenderer

import pygame
import pygame_gui
import numpy as np

import matplotlib

matplotlib.use("Agg")


class Game:
    def __init__(self,
                 forest: Forest,
                 width: int = 1234,
                 height: int = 900,
                 fps: int = 60) -> None:
        pygame.init()
        pygame.display.set_caption("Symulacja Pożaru Lasu")

        self.width = width
        self.height = height
        self.fps = fps
        self.running = True

        self.window_surface = pygame.display.set_mode((self.width, self.height))
        self.manager = pygame_gui.UIManager((self.width, self.height), 'config/theme.json')
        self.clock = pygame.time.Clock()

        self.forest = forest
        self.single_block_size = self.height // self.forest.size

        # UI Components
        self.left_panel = LeftPanel(self.manager, self.width, self.height)
        self.humidity_renderer = HumidityRenderer(size=(4, 4), dpi=100)

        self.grid_surface = pygame.Surface((self.forest.size, self.forest.size))
        self.humidity_surface = self.update_humidity_surface()

    def update_humidity_surface(self):
        return self.humidity_renderer.draw_humidity(self.forest.humidity)

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.USEREVENT:
                if (event.user_type == pygame_gui.UI_BUTTON_PRESSED
                        and event.ui_element == self.left_panel.restart_button):
                    self.forest = self.forest.simulation_reset()

            self.manager.process_events(event)

    def update(self, time_delta):
        self.forest.next_gen(pygame.time.get_ticks())
        self.humidity_surface = self.update_humidity_surface()
        self.manager.update(time_delta)

    def render(self):
        self.window_surface.fill((24, 24, 24))

        self.render_forest_grid()

        self.render_left_panel()

        self.manager.draw_ui(self.window_surface)

        pygame.display.flip()

    def render_forest_grid(self):
        color_array = self.get_color_array()
        pygame.surfarray.blit_array(self.grid_surface, color_array)
        scaled_size = (self.forest.size * self.single_block_size,
                       self.forest.size * self.single_block_size)
        scaled_grid = pygame.transform.scale(self.grid_surface, scaled_size)
        self.window_surface.blit(scaled_grid, (400, 66))

    def render_left_panel(self):
        self.window_surface.blit(self.humidity_surface, (-4, 500))
        self.left_panel.draw_wind_compass(self.window_surface, self.forest)

    def get_color_array(self) -> np.ndarray:
        grid_flat = self.forest.grid.flatten()
        humidity_flat = self.forest.humidity.flatten()
        size = self.forest.size

        colors = np.zeros((size ** 2, 3), dtype=np.uint8)

        # Type.EMPTY
        colors[grid_flat == Type.EMPTY] = [220, 220, 220]

        # Type.TREE
        green_intensity = np.clip(
            (120 / humidity_flat[grid_flat == Type.TREE]).astype(np.uint8),
            0, 255
        )
        colors[grid_flat == Type.TREE] = np.stack([
            np.zeros_like(green_intensity),
            green_intensity,
            np.zeros_like(green_intensity)
        ], axis=1)

        # Type.BURNING
        colors[grid_flat == Type.BURNING] = [220, 0, 0]

        # Type.LIGHTNING
        colors[grid_flat == Type.LIGHTNING] = [100, 100, 220]

        # Type.ASH
        colors[grid_flat == Type.ASH] = [50, 50, 50]

        # Type.WATER
        colors[grid_flat == Type.WATER] = [150, 150, 250]

        return colors.reshape((size, size, 3))

    def start(self) -> None:
        while self.running:
            time_delta = self.clock.tick(self.fps) / 1000.0

            self.process_events()
            self.update(time_delta)
            self.render()
