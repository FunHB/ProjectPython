import pygame

from forest import Forest
from forest import Type


class Game:
    def __init__(self, forest: Forest) -> None:
        pygame.init()

        self.fps = 10
        self.block_size = 800 // forest.size

        self.size = self.block_size * forest.size
        self.screen = pygame.display.set_mode((self.size, self.size))
        self.clock = pygame.time.Clock()
        self.running = True
        self.forest = forest

    def start(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill("white")

            # Game Render            
            self.draw_grid()
            self.forest.next_gen(pygame.time.get_ticks())

            pygame.display.flip()
            self.clock.tick(self.fps)

    def draw_grid(self) -> None:
        for x in range(0, self.size, self.block_size):
            for y in range(0, self.size, self.block_size):
                rect = pygame.Rect(x, y, self.block_size, self.block_size)
                pos = (x // self.block_size, y // self.block_size)
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
