import numpy as np
import pandas as pd
from enum import Enum

class Type(Enum):
    EMPTY = 0
    TREE = 1
    BURNING = 2

class Forest:
    def __init__(self, size: int,
                 tree_density: float,
                 lightning_prob: float,
                 growth_prob: float,
                 spread_prob: float,
                 radius: int) -> None:
        self.size = size
        self.tree_density = tree_density
        self.lightning_prob = lightning_prob
        self.growth_prob = growth_prob
        self.spread_prob = spread_prob
        self.radius = radius

        self.grid = self.initialize_grid()
        self.history = pd.DataFrame(columns=['step', 'burning', 'tree', 'empty'])

    def initialize_grid(self) -> np.ndarray:
        grid = np.random.choice([Type.EMPTY, Type.TREE],
                                size=(self.size, self.size),
                                p=[1 - self.tree_density, self.tree_density])
        return grid

    def fire_neighbors_check(self, idx: int, jdx: int) -> bool:
        for di in range(-self.radius, self.radius + 1):
            for dj in range(-self.radius, self.radius + 1):
                if di == 0 and dj == 0:
                    continue

                ni, nj = idx + di, jdx + dj
                if 0 <= ni < self.size and 0 <= nj < self.size:
                    if self.grid[ni, nj] == Type.BURNING:
                        return True
        return False

    def step(self, step_num: int) -> None:
        new_grid = self.grid.copy()

        for i in range(self.size):
            for j in range(self.size):

                if self.grid[i, j] == Type.BURNING:
                    # Płonące drzewo po tym kroku staje się puste
                    new_grid[i, j] = Type.EMPTY
                else:
                    if self.grid[i, j] == Type.TREE:
                        # Szansa zapalenia od pioruna
                        if np.random.rand() < self.lightning_prob:
                            new_grid[i, j] = Type.BURNING
                        # Szansa zapalenia od sąsiada
                        elif self.fire_neighbors_check(i, j):
                            if np.random.rand() < self.spread_prob:
                                new_grid[i, j] = Type.BURNING
                    else:  # EMPTY
                        if np.random.rand() < self.growth_prob:
                            new_grid[i, j] = Type.TREE

        self.grid = new_grid

        burning_count = np.count_nonzero(self.grid == Type.BURNING)
        tree_count = np.count_nonzero(self.grid == Type.TREE)
        empty_count = np.count_nonzero(self.grid == Type.EMPTY)

        new_row = pd.DataFrame({
            'step': [step_num],
            'burning': [burning_count],
            'tree': [tree_count],
            'empty': [empty_count]
        })
        self.history = pd.concat([self.history, new_row], ignore_index=True)