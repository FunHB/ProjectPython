from typing import Any

import numpy as np
import scipy.stats as stats
from scipy.ndimage import gaussian_filter
import pandas as pd
import pygame
import struct
from enum import IntEnum

import compushady
import compushady.formats
from compushady import HEAP_READBACK, Buffer, Texture2D, HEAP_UPLOAD, Compute
from compushady.shaders import hlsl

compushady.config.set_debug(True)


class Type(IntEnum):
    EMPTY = 0
    TREE = 1
    BURNING = 2
    LIGHTNING = 3
    ASH = 4


class Forest:
    def __init__(self, size: int, tree_density: float, lightning_prob: float, growth_prob: float,
                 spread_prob: float, wind: pygame.Vector2, wind_change: float, radius: int) -> None:
        self.size = size
        self.tree_density = tree_density
        self.lightning_prob = lightning_prob
        self.growth_prob = growth_prob
        self.spread_prob = spread_prob
        self.wind = pygame.Vector2(wind).normalize()
        self.wind_change = wind_change
        self.radius = radius

        self.rng = np.random.default_rng()  # Seed do rng
        self.grid = self.initialize_grid()
        self.new_grid = self.grid.copy()
        self.humidity = self.initialize_humidity(5, 15, (25, 75), 50)
        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])

        self.shader = hlsl.compile(open('./shader.hlsl').read())

        self.humidity_texture = Texture2D(
            size, size, compushady.formats.R32_FLOAT)
        humidity_buffer = Buffer(self.humidity_texture.size, HEAP_UPLOAD)

        humidity_buffer.upload(
            b''.join([struct.pack('f', float(x)) for x in list(self.humidity.flatten())]))
        humidity_buffer.copy_to(self.humidity_texture)

        config = Buffer(96, HEAP_UPLOAD)
        self.config_fast = Buffer(config.size)

        config.upload(struct.pack('fff', growth_prob,
                      spread_prob, lightning_prob))
        config.copy_to(self.config_fast)

        self.wind_config = Buffer(64, HEAP_UPLOAD)
        self.wind_buffer = Buffer(self.wind_config.size)

        self.source = Texture2D(self.size, self.size,
                                compushady.formats.R8_UINT)
        self.source_buffer = Buffer(self.source.size, HEAP_UPLOAD)

        self.noise = Texture2D(self.size, self.size,
                               compushady.formats.R32_FLOAT)
        self.noise_buffer = Buffer(self.noise.size, HEAP_UPLOAD)

        self.target = Texture2D(self.size, self.size,
                                compushady.formats.R8_UINT)
        self.target_buffer = Buffer(self.target.size, HEAP_READBACK)

        self.compute = Compute(self.shader, cbv=[self.config_fast, self.wind_buffer], srv=[
                               self.source, self.humidity_texture, self.noise], uav=[self.target])

    def initialize_humidity(self, min_clusters=3, max_clusters=10, sigma_range=(5, 25), noise_scale=10) -> np.ndarray:
        x, y = np.meshgrid(np.linspace(0, self.size, self.size),
                           np.linspace(0, self.size, self.size))

        # Randomize the number of clusters
        num_clusters = np.random.randint(min_clusters, max_clusters + 1)

        # Randomize cluster parameters
        centers = [(np.random.uniform(0, x.__len__()), np.random.uniform(
            0, y.__len__())) for _ in range(num_clusters)]
        amplitudes = [np.random.uniform(0.5, 1) for _ in range(num_clusters)]
        sigmas = [(np.random.uniform(*sigma_range), np.random.uniform(*sigma_range))
                  for _ in range(num_clusters)]

        # Create Perlin-like noise
        noise_x = gaussian_filter(np.random.rand(*x.shape), sigma=noise_scale)
        noise_y = gaussian_filter(np.random.rand(*y.shape), sigma=noise_scale)

        # Generate clusters
        result = np.zeros_like(x)
        for (cx, cy), A, (sigma_x, sigma_y) in zip(centers, amplitudes, sigmas):
            wobble_x = cx + noise_x
            wobble_y = cy + noise_y
            result += A * \
                np.exp(-((x - wobble_x)**2 / (2 * sigma_x**2) +
                       (y - wobble_y)**2 / (2 * sigma_y**2)))

        return .5 + np.clip(result / np.max(result), 0, 1)

    def initialize_grid(self) -> np.ndarray:
        return self.rng.choice(
            np.array([Type.EMPTY, Type.TREE]),
            size=(self.size, self.size),
            p=[1 - self.tree_density, self.tree_density]
        )

    def simulation_reset(self) -> None:
        self.grid = self.initialize_grid()
        self.humidity = self.initialize_humidity(5, 15, (25, 50), 50)
        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])

    def next_gen(self, current_frame: int = None) -> None:
        self.source_buffer.upload(bytes(list(self.grid.flatten())))
        self.source_buffer.copy_to(self.source)

        noise = np.clip(self.rng.uniform(0, 1, size=(self.size**2)), 0, 1)

        self.noise_buffer.upload(b''.join([struct.pack('f', float(x)) for x in noise]))
        self.noise_buffer.copy_to(self.noise)

        # print(noise)

        self.wind_config.upload(struct.pack('ff', float(self.wind.x), float(self.wind.y)))
        self.wind_config.copy_to(self.wind_buffer)

        self.compute.dispatch(self.size // 16, self.size // 16, 1)

        self.target.copy_to(self.target_buffer)
        array = np.array(list(self.target_buffer.readback())
                         ).reshape(self.size, self.size)

        self.grid = array

        # for i in range(self.size):
        #     for j in range(self.size):
        #         new_grid[i, j] = self.next_state((i, j))

        # self.grid = new_grid

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

    # def neighbors_check(self, position: tuple[int, int], type_check: Type, radius: int = 1) -> pygame.Vector2 | None:
    #         x, y = position

    #         for di in range(-radius, radius + 1):
    #             for dj in range(-radius, radius + 1):
    #                 if di == 0 and dj == 0:
    #                     continue

    #                 ni, nj = x + di, y + dj
    #                 if 0 <= ni < self.size and 0 <= nj < self.size:
    #                     if self.grid[ni, nj] == type_check:
    #                         return ni, nj
    #         return None

    # def next_state(self, pos: tuple[int, int]) -> Type:
    #     # Any -> Lightning
    #     if self.rng.random() < self.lightning_prob:
    #         return Type.LIGHTNING

    #     current_type = self.grid[pos]

    #     # Lightning -> Burning
    #     if current_type == Type.LIGHTNING:
    #         return Type.BURNING

    #     # Burning -> Ash
    #     if current_type == Type.BURNING:
    #         if self.rng.random() < (2 - self.humidity[pos]):
    #             return Type.ASH

    #     # ASH -> Empty
    #     if current_type == Type.ASH:
    #         return Type.EMPTY

    #     # Empty -> Tree
    #     if current_type == Type.EMPTY:
    #         if self.neighbors_check(pos, Type.TREE, self.radius) and self.rng.random() < self.growth_prob:
    #             # self.humidity[pos] = np.clip(self.humidity[pos] + self.rng.random() * (.1 - .01) + .01, .5, 1.5)
    #             return Type.TREE

    #     # Tree -> Burning
    #     if current_type == Type.TREE:
    #         fire_pos = self.neighbors_check(pos, Type.BURNING, self.radius)
    #         if fire_pos:
    #             fire = (pygame.Vector2(fire_pos) -
    #                     pygame.Vector2(pos)).normalize()
    #             angle = np.arccos(fire.dot(self.wind))

    #             if self.rng.random() < self.spread_prob * (2 - self.humidity[pos]) * (angle / np.pi):
    #                 # self.humidity[pos] = np.clip(self.humidity[pos] - self.rng.random() * (.1 - .01) + .01, .5, 1.5)
    #                 return Type.BURNING

    #     # Default
    #     return current_type
