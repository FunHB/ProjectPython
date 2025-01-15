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
        self.window_surface = pygame.display.set_mode(
            (self.width, self.height))
        self.manager = pygame_gui.UIManager(
            (self.width, self.height), 'theme.json')
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True

        self.single_block_size = 4
        self.forest = forest

        self.left_panel = self.initialize_left_panel()

        self.grid_surface = pygame.Surface((forest.size, forest.size))
        self.grid_pixels = np.zeros(
            (forest.size, forest.size, 3), dtype=np.uint8)

    def initialize_left_panel(self):
        panel = {'rect': pygame.Rect((0, 0), (400, self.height)),
                 'title_1': pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 50), (380, 200)),
                                                        text="Symulacja",
                                                        manager=self.manager),
                 'title_2': pygame_gui.elements.UILabel(relative_rect=pygame.Rect((10, 115), (380, 200)),
                                                        text="Pożaru Lasu",
                                                        manager=self.manager),
                 'restart_button': pygame_gui.elements.UIButton(relative_rect=pygame.Rect((100, 540), (200, 50)),
                                                                text="Restart",
                                                                manager=self.manager)}

        return panel

    def process_events(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.left_panel['restart_button']:
                    self.forest.simulation_reset()

    def start(self) -> None:
        while self.running:
            time_delta = self.clock.tick(self.fps) / 1000.0

            for event in pygame.event.get():
                self.process_events(event)
                self.manager.process_events(event)

            self.manager.update(time_delta)

            # Aktualizacja stanu lasu
            self.forest.next_gen(pygame.time.get_ticks())

            # Aktualizacja kolorów pikseli
            color_array = self.get_color_array()
            pygame.surfarray.blit_array(self.grid_surface, color_array)
            scaled_size = (self.forest.size * self.single_block_size,
                           self.forest.size * self.single_block_size)
            scaled_grid = pygame.transform.scale(
                self.grid_surface, scaled_size)

            # Render wind compass
            wind_surface = pygame.surface.Surface((150, 150))
            wind_surface.fill(pygame.Color(24, 24, 24))
            wind_center = pygame.Vector2(wind_surface.width / 2, wind_surface.height / 2)
            wind_vector = pygame.Vector2(self.forest.wind) * 125
            pygame.draw.circle(wind_surface, pygame.Color(50, 50, 50), wind_center, 75)
            draw_arrow(wind_surface, wind_center - (wind_vector / 2),
                       wind_center + (wind_vector / 2), [220, 0, 0], 2, 20, 10)

            # Renderowanie GUI
            self.window_surface.fill((24, 24, 24))
            self.window_surface.blit(scaled_grid, (400, 50))
            self.window_surface.blit(wind_surface, (self.width - 400 + 100, self.height / 2 - 100))
            self.manager.draw_ui(self.window_surface)

            pygame.display.flip()

    def get_color_array(self) -> np.ndarray:
        grid_flat = self.forest.grid.flatten()
        humidity_flat = self.forest.humidity.flatten()

        colors = np.zeros((self.forest.size ** 2, 3), dtype=np.uint8)

        # Type.EMPTY
        colors[grid_flat == Type.EMPTY] = [220, 220, 220]

        # Type.TREE
        green_intensity = np.clip(
            (120 / humidity_flat[grid_flat == Type.TREE]).astype(np.uint8), 0, 255)
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


def draw_arrow(
    surface: pygame.Surface,
    start: pygame.Vector2,
    end: pygame.Vector2,
    color: pygame.Color,
    body_width: int = 2,
    head_width: int = 4,
    head_height: int = 2,
):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - head_height

    # Create the triangle head around the origin
    head_verts = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]
    # Rotate and translate the head into place
    translation = pygame.Vector2(
        0, arrow.length() - (head_height / 2)).rotate(-angle)
    for i in range(len(head_verts)):
        head_verts[i].rotate_ip(-angle)
        head_verts[i] += translation
        head_verts[i] += start

    pygame.draw.polygon(surface, color, head_verts)

    # Stop weird shapes when the arrow is shorter than arrow head
    if arrow.length() >= head_height:
        # Calculate the body rect, rotate and translate into place
        body_verts = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
        for i in range(len(body_verts)):
            body_verts[i].rotate_ip(-angle)
            body_verts[i] += translation
            body_verts[i] += start

        pygame.draw.polygon(surface, color, body_verts)
