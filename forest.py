from typing import Any

import numpy as np
import scipy.stats as stats
import pandas as pd
from enum import Enum


class Type(Enum):
    EMPTY = 0
    TREE = 1
    BURNING = 2
    LIGHTNING = 3
    ASH = 4


class Forest:
    def __init__(self, size: int, tree_density: float, lightning_prob: float, growth_prob: float,
                 spread_prob: float, wind: np.ndarray, radius: int) -> None:
        self.size = size
        self.tree_density = tree_density
        self.lightning_prob = lightning_prob
        self.growth_prob = growth_prob
        self.spread_prob = spread_prob
        self.wind = wind
        self.radius = radius

        self.rng = np.random.default_rng(40)  # Seed do rng
        self.grid = self.initialize_grid()
        self.humidity = self.initialize_humidity()
        self.history = pd.DataFrame(columns=['step', 'burning', 'tree', 'empty'])

    def initialize_humidity(self) -> np.ndarray:
        mu, sigma = 1, .2
        min_val, max_val = 0.5, 1.5
        return stats.truncnorm(
            (min_val - mu) / sigma, (max_val - mu) / sigma, loc=mu, scale=sigma
        ).rvs(size=(self.size, self.size), random_state=self.rng)

    def initialize_grid(self) -> np.ndarray:
        return self.rng.choice(
            np.array([Type.EMPTY, Type.TREE]),
            size=(self.size, self.size),
            p=[1 - self.tree_density, self.tree_density]
        )

    def simulation_reset(self) -> None:
        self.grid = self.initialize_grid()
        self.humidity = self.initialize_humidity()
        self.history = pd.DataFrame(columns=['step', 'burning', 'tree', 'empty'])

    def neighbors_check(self, position: tuple[int, int], type_check: Type, radius: int = 1) -> tuple[int, int] | None:
        x, y = position

        for di in range(-radius, radius + 1):
            for dj in range(-radius, radius + 1):
                if di == 0 and dj == 0:
                    continue

                ni, nj = x + di, y + dj
                if 0 <= ni < self.size and 0 <= nj < self.size:
                    if self.grid[ni, nj] == type_check:
                        return ni, nj
        return None

    def next_state(self, pos: tuple[int, int]) -> Type | np.ndarray[tuple[int, ...], Any]:
        # Any -> Lightning
        if self.rng.random() < self.lightning_prob:
            return Type.LIGHTNING

        current_type = self.grid[pos]

        # Lightning -> Burning
        if current_type == Type.LIGHTNING:
            return Type.BURNING

        # Burning -> Ash
        if current_type == Type.BURNING:
            return Type.ASH

        # ASH -> Empty
        if current_type == Type.ASH:
            return Type.EMPTY

        # Empty -> Tree
        if current_type == Type.EMPTY:
            if self.neighbors_check(pos, Type.TREE, self.radius) and self.rng.random() < self.growth_prob:
                return Type.TREE

        # Tree -> Burning
        if current_type == Type.TREE:
            if self.neighbors_check(pos, Type.BURNING, self.radius):
                fire_vector = np.array(self.neighbors_check(pos, Type.BURNING, self.radius)) - np.array(pos)
                angle = np.arccos(
                    np.dot(fire_vector, self.wind) /
                    (np.linalg.norm(fire_vector) * np.linalg.norm(self.wind))
                )
                if self.rng.random() < self.spread_prob * self.humidity[pos] * angle / np.pi:
                    return Type.BURNING

        # Default
        return current_type

    def next_gen(self, current_frame: int = None) -> None:
        new_grid = self.grid.copy()

        for i in range(self.size):
            for j in range(self.size):
                new_grid[i, j] = self.next_state((i, j))

        self.grid = new_grid

        burning_count = np.count_nonzero(self.grid == Type.BURNING)
        tree_count = np.count_nonzero(self.grid == Type.TREE)
        empty_count = np.count_nonzero(self.grid == Type.EMPTY)

        if current_frame is not None:
            new_row = pd.DataFrame({
                'step': [current_frame],
                'burning': [burning_count],
                'tree': [tree_count],
                'empty': [empty_count]
            })
            self.history = pd.concat([self.history, new_row], ignore_index=True)
