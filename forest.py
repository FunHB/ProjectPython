import numpy as np
import pandas as pd
from enum import Enum


class Type(Enum):
    EMPTY = 0
    TREE = 1
    BURNING = 2
    LIGHTNINT = 3
    FOLIAGE = 4


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
        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])


    def initialize_grid(self) -> np.ndarray:
        grid = np.random.choice([Type.EMPTY, Type.TREE],
                                size=(self.size, self.size),
                                p=[1 - self.tree_density, self.tree_density])
        return grid


    def neighbors_check(self, idx: int, jdx: int, type: Type, radius=1) -> bool:
        for di in range(-radius, radius + 1):
            for dj in range(-radius, radius + 1):
                if di == 0 and dj == 0:
                    continue

                ni, nj = idx + di, jdx + dj
                if 0 <= ni < self.size and 0 <= nj < self.size:
                    if self.grid[ni, nj] == type:
                        return True
        return False


    def next_state(self, position: tuple[int, int]) -> Type:
        # Burning -> Empty
        if self.grid[position] == Type.BURNING:
            return Type.EMPTY
        
        # Lightning -> Burning
        if self.grid[position] == Type.LIGHTNINT:
            return Type.BURNING
            
        # Empty -> Tree
        if self.grid[position] == Type.EMPTY:
            if self.neighbors_check(position, Type.TREE, self.radius):
                return Type.TREE
        
        # Tree -> Burning
        if self.grid[position] == Type.TREE:
            if self.neighbors_check(position, Type.BURNING, self.radius) and np.random.rand() < self.spread_prob:
                return Type.BURNING
        
        # Any -> Lightning
        if np.random.rand() < self.lightning_prob:
            return Type.LIGHTNINT
        

    def frame(self, current_frame: int = None) -> None:
        new_grid = self.grid.copy()
    
        for i in range(self.size):
            for j in range(self.size):
                new_grid[i, j] = self.next_state(i, j)

        self.grid = new_grid

        burning_count = np.count_nonzero(self.grid == Type.BURNING)
        tree_count = np.count_nonzero(self.grid == Type.TREE)
        empty_count = np.count_nonzero(self.grid == Type.EMPTY)

        if (current_frame != None):
            new_row = pd.DataFrame({
                'step': [current_frame],
                'burning': [burning_count],
                'tree': [tree_count],
                'empty': [empty_count]
            })
            self.history = pd.concat([self.history, new_row], ignore_index=True)
        