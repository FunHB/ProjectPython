from .arrow import draw_arrow

import pygame
import pygame_gui
import numpy as np
import pylab
import matplotlib.backends.backend_agg as agg
import matplotlib

matplotlib.use("Agg")


class LeftPanel:
    def __init__(self, manager, width, height):
        self.width = width
        self.height = height

        self.rect = pygame.Rect((0, 0), (self.width, self.height))
        self.title_1 = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 10), (380, 200)),
            text="Symulacja",
            manager=manager
        )
        self.title_2 = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 70), (380, 200)),
            text="Pożaru Lasu",
            manager=manager
        )
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((100, 240), (200, 50)),
            text="Restart",
            manager=manager
        )

    def draw_wind_compass(self, window_surface, forest):
        wind_surface = pygame.surface.Surface((150, 150))
        wind_surface.fill(pygame.Color(24, 24, 24))

        wind_center = pygame.Vector2(wind_surface.get_width() / 2,
                                     wind_surface.get_height() / 2)
        wind_vector = -pygame.Vector2(forest.wind.y, forest.wind.x) * 125

        pygame.draw.circle(wind_surface, pygame.Color(50, 50, 50), wind_center, 75)

        start_pos = wind_center - (wind_vector / 2)
        end_pos = wind_center + (wind_vector / 2)
        draw_arrow(wind_surface, start_pos, end_pos, pygame.Color(220, 0, 0), 2, 20, 10)

        window_surface.blit(wind_surface, (124, self.height / 2 - 100))


class HumidityRenderer:
    def __init__(self, size=(4, 4), dpi=100):
        self.figure = pylab.figure(figsize=size, dpi=dpi)
        self.figure.patch.set_alpha(0)
        self.ax = self.figure.gca()
        self.setup_plot()

    def setup_plot(self):
        self.ax.set_facecolor((24/255, 24/255, 24/255))
        for axis in ['top', 'bottom', 'left', 'right']:
            self.ax.spines[axis].set_linewidth(0)
        self.ax.axes.get_xaxis().set_ticks([])
        self.ax.axes.get_yaxis().set_ticks([])

    def draw_humidity(self, humidity):
        self.ax.clear()
        self.setup_plot()
        self.ax.imshow(
            np.flipud(np.rot90(2 - humidity)),
            cmap="viridis"
        )

        canvas = agg.FigureCanvasAgg(self.figure)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_argb()
        size = canvas.get_width_height()
        return pygame.image.frombytes(raw_data, size, "ARGB")
