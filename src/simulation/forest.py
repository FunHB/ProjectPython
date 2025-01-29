from src.simulation.types import Type
from src.simulation.helpers import generate_cluster_map
from src.simulation.gpu_compute import ForestComputeEngine

from typing_extensions import Self

import numpy as np
import pandas as pd
import pygame


class Forest:
    def __init__(
            self,
            tree_density: float,
            lightning_prob: float,
            growth_prob: float,
            spread_prob: float,
            humidity_change: float,
            humidity_change_fire: float,
            water_threshold: float,
            wind: pygame.Vector2,
            wind_change: float,
            radius: int,
            # Parametry GPU
            size: int = 256,
            shader_path: str = "src/simulation/shader.hlsl",
            # RNG seed
            seed: int = None
    ) -> None:
        self.size = size
        self.tree_density = tree_density
        self.lightning_prob = lightning_prob
        self.growth_prob = growth_prob
        self.spread_prob = spread_prob
        self.humidity_change = humidity_change
        self.humidity_change_fire = humidity_change_fire
        self.water_threshold = water_threshold

        self.wind = pygame.Vector2(wind).normalize()
        self.wind_change = wind_change
        self.radius = radius
        self.rng = np.random.default_rng(seed)

        self.humidity = self.initialize_humidity()
        self.grid = self.initialize_grid()

        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])

        self.compute_engine = ForestComputeEngine(
            shader_path=shader_path,
            size=self.size,
            growth_prob=self.growth_prob,
            spread_prob=self.spread_prob,
            lightning_prob=self.lightning_prob,
            humidity_change=self.humidity_change,
            humidity_change_fire=self.humidity_change_fire
        )

    def initialize_humidity(self):
        base = generate_cluster_map(
            self.rng,
            self.size,
            min_clusters=15,
            max_clusters=20,
            sigma_range=(20, 50),
            noise_scale=25
        )
        return 0.5 + base

    def initialize_grid(self) -> np.ndarray:
        cluster = generate_cluster_map(
            self.rng,
            self.size,
            min_clusters=15,
            max_clusters=20,
            sigma_range=(20, 50),
            noise_scale=50
        )
        trees = (
                (cluster + self.rng.normal(0, 0.1, size=(self.size, self.size)))
            >= self.tree_density
        )

        grid = np.zeros((self.size, self.size), dtype=np.uint8)
        grid[trees] = Type.TREE
        grid[self.humidity >= self.water_threshold] = Type.WATER
        return grid

    def simulation_reset(self) -> Self:
        return Forest(tree_density=self.tree_density,
                      lightning_prob=self.lightning_prob,
                      growth_prob=self.growth_prob,
                      spread_prob=self.spread_prob,
                      humidity_change=self.humidity_change,
                      humidity_change_fire=self.humidity_change_fire,
                      water_threshold=self.water_threshold,
                      wind=self.wind,
                      wind_change=self.wind_change,
                      radius=self.radius)

    def compute_next_gen(self):
        self.compute_engine.update_humidity(self.humidity)
        self.compute_engine.update_grid(self.grid)

        noise = self.rng.uniform(0, 1, size=(self.size**2))
        self.compute_engine.update_noise(noise)

        self.compute_engine.update_wind(self.wind.x, self.wind.y)

        self.compute_engine.dispatch()

        new_grid, delta_humidity = self.compute_engine.read_results()
        return new_grid, delta_humidity

    def next_gen(self, current_frame: int = None) -> None:
        new_grid, delta_humidity = self.compute_next_gen()

        self.grid = new_grid
        self.humidity = np.clip(
            self.humidity + delta_humidity,
            0.5,
            1.5
        )

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
            self.history = pd.concat(
                [self.history, new_row], ignore_index=True)

        self.wind = self.wind.rotate(
            (2 * self.rng.random() - 1) * self.wind_change)
