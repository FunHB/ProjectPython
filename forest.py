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

# compushady.config.set_debug(True)


class Type(IntEnum):
    EMPTY = 0
    TREE = 1
    BURNING = 2
    LIGHTNING = 3
    ASH = 4


class Forest:
    def __init__(self, tree_density: float, lightning_prob: float, growth_prob: float,
                 spread_prob: float, wind: pygame.Vector2, wind_change: float, radius: int) -> None:
        self.size = 256
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
        self.humidity = self.initialize_humidity()
        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])


        # Initialize Compute Shader
        self.shader = hlsl.compile(open('./shader.hlsl').read())

        self.humidity_texture = Texture2D(self.size, self.size, compushady.formats.R32_FLOAT)
        self.humidity_buffer = Buffer(self.humidity_texture.size, HEAP_UPLOAD)

        self.humidity_buffer.upload(b''.join([struct.pack('f', float(x)) for x in list(self.humidity.flatten())]))
        self.humidity_buffer.copy_to(self.humidity_texture)

        config = Buffer(96, HEAP_UPLOAD)
        self.config_fast = Buffer(config.size)

        config.upload(struct.pack('fff', growth_prob, spread_prob, lightning_prob))
        config.copy_to(self.config_fast)

        self.wind_config = Buffer(64, HEAP_UPLOAD)
        self.wind_buffer = Buffer(self.wind_config.size)

        self.source = Texture2D(self.size, self.size, compushady.formats.R8_UINT)
        self.source_buffer = Buffer(self.source.size, HEAP_UPLOAD)

        self.noise = Texture2D(self.size, self.size, compushady.formats.R32_FLOAT)
        self.noise_buffer = Buffer(self.noise.size, HEAP_UPLOAD)

        self.target = Texture2D(self.size, self.size, compushady.formats.R8_UINT)
        self.target_buffer = Buffer(self.target.size, HEAP_READBACK)

        self.compute = Compute(self.shader, cbv=[self.config_fast, self.wind_buffer], srv=[self.source, self.humidity_texture, self.noise], uav=[self.target])

    def initialize_humidity(self, min_clusters=15, max_clusters=20, sigma_range=(20, 50), noise_scale=25) -> np.ndarray:
        x, y = np.meshgrid(np.linspace(0, self.size, self.size), np.linspace(0, self.size, self.size))

        # Randomize the number of clusters
        num_clusters = np.random.randint(min_clusters, max_clusters + 1)

        # Randomize cluster parameters
        centers = [(np.random.uniform(0, x.__len__()), np.random.uniform(0, y.__len__())) for _ in range(num_clusters)]
        amplitudes = [np.random.uniform(0.5, 1) for _ in range(num_clusters)]
        sigmas = [(np.random.uniform(*sigma_range), np.random.uniform(*sigma_range))for _ in range(num_clusters)]

        # Create Perlin-like noise
        noise_x = gaussian_filter(np.random.rand(*x.shape), sigma=noise_scale)
        noise_y = gaussian_filter(np.random.rand(*y.shape), sigma=noise_scale)

        # Generate clusters
        result = np.zeros_like(x)
        for (cx, cy), A, (sigma_x, sigma_y) in zip(centers, amplitudes, sigmas):
            wobble_x = cx + noise_x
            wobble_y = cy + noise_y
            result += A * np.exp(-((x - wobble_x)**2 / (2 * sigma_x**2) + (y - wobble_y)**2 / (2 * sigma_y**2)))

        return .5 + np.clip(result / np.max(result), 0, 1)

    def initialize_grid(self) -> np.ndarray:
        return self.rng.choice(
            np.array([Type.EMPTY, Type.TREE]),
            size=(self.size, self.size),
            p=[1 - self.tree_density, self.tree_density]
        )

    def simulation_reset(self) -> None:
        self.grid = self.initialize_grid()
        self.humidity = self.initialize_humidity()

        self.humidity_buffer.upload(
            b''.join([struct.pack('f', float(x)) for x in list(self.humidity.flatten())]))
        self.humidity_buffer.copy_to(self.humidity_texture)

        self.history = pd.DataFrame(
            columns=['step', 'burning', 'tree', 'empty'])

    def compute_next_gen(self):
        # Send grid
        self.source_buffer.upload(bytes(list(self.grid.flatten())))
        self.source_buffer.copy_to(self.source)

        # Send noise texture
        noise = np.clip(self.rng.uniform(0, 1, size=(self.size**2)), 0, 1)

        self.noise_buffer.upload(b''.join([struct.pack('f', float(x)) for x in noise]))
        self.noise_buffer.copy_to(self.noise)

        # Send wind vector
        self.wind_config.upload(struct.pack('ff', self.wind.x, self.wind.y))
        self.wind_config.copy_to(self.wind_buffer)

        # Get new grid
        self.compute.dispatch(self.size // 16, self.size // 16, 1)

        self.target.copy_to(self.target_buffer)
        array = np.array(list(self.target_buffer.readback())).reshape(self.size, self.size)

        return array

    def next_gen(self, current_frame: int = None) -> None:
        self.grid = self.compute_next_gen()

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
