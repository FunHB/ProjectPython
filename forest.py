import numpy as np
import scipy.stats as stats
import pandas as pd
from enum import Enum


class Type(Enum):
    EMPTY = 0
    TREE = 1
    BURNING = 2
    LIGHTNINT = 3
    ASH = 4


class Forest:
    def __init__(self, size: int,
                 tree_density: float,
                 lightning_prob: float,
                 growth_prob: float,
                 spread_prob: float,
                 wind: np.ndarray,
                 radius: int) -> None:
        self.size = size
        self.tree_density = tree_density
        self.lightning_prob = lightning_prob
        self.growth_prob = growth_prob
        self.spread_prob = spread_prob
        self.wind = wind
        self.radius = radius

        self.grid = self.initialize_grid()
        self.humidity = self.initialize_humidity()
        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])


    def initialize_humidity(self) -> np.ndarray:
        mu, sigma = 1, .2        
        min, max = 0.5, 1.5
        return stats.truncnorm((min - mu) / sigma, (max - mu) / sigma, loc=mu, scale=sigma).rvs(size=(self.size, self.size))
    

    def initialize_grid(self) -> np.ndarray:
        grid = np.random.choice([Type.EMPTY, Type.TREE],
                                size=(self.size, self.size),
                                p=[1 - self.tree_density, self.tree_density])
        return grid


    def neighbors_check(self, position, type: Type, radius=1) -> bool:
        x, y = position
        
        for di in range(-radius, radius + 1):
            for dj in range(-radius, radius + 1):
                if di == 0 and dj == 0:
                    continue

                ni, nj = x + di, y + dj
                if 0 <= ni < self.size and 0 <= nj < self.size:
                    if self.grid[ni, nj] == type:
                        return (ni, nj)
        return None


    def next_state(self, pos: tuple[int, int]) -> Type:
        # Any -> Lightning
        if np.random.rand() < self.lightning_prob:
            return Type.LIGHTNINT
        
        # Lightning -> Burning
        if self.grid[pos] == Type.LIGHTNINT:
            return Type.BURNING
        
        # Burning -> Ash
        if self.grid[pos] == Type.BURNING:
            return Type.ASH
            
        # ASH -> Empty
        if self.grid[pos] == Type.ASH:
            return Type.EMPTY
            
        # Empty -> Tree
        if self.grid[pos] == Type.EMPTY:
            if self.neighbors_check(pos, Type.TREE, self.radius) and np.random.rand() < self.growth_prob:
                return Type.TREE
        
        # Tree -> Burning
        if self.grid[pos] == Type.TREE:
            if (self.neighbors_check(pos, Type.BURNING, self.radius)):
                fire_vector = np.array(self.neighbors_check(pos, Type.BURNING, self.radius)) - np.array(pos)
                angle = np.arccos(np.dot(fire_vector, self.wind) / (np.linalg.norm(fire_vector) * np.linalg.norm(self.wind)))
                
                if np.random.rand() < self.spread_prob * self.humidity[pos] * angle / np.pi:
                    return Type.BURNING
        
        # Default
        return self.grid[pos]
        

    def next_gen(self, current_frame: int = None) -> None:
        new_grid = self.grid.copy()
    
        for i in range(self.size):
            for j in range(self.size):
                new_grid[i, j] = self.next_state((i, j))

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
        