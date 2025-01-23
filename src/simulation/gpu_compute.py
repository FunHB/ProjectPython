import struct
from typing import Any

import numpy as np
import compushady
import compushady.formats
from compushady import HEAP_READBACK, Buffer, Texture2D, HEAP_UPLOAD, Compute
from compushady.shaders import hlsl
from numpy import ndarray


class ForestComputeEngine:
    def __init__(self,
                 shader_path: str,
                 size: int,
                 growth_prob: float,
                 spread_prob: float,
                 lightning_prob: float,
                 humidity_change: float,
                 humidity_change_fire: float) -> None:

        self.size = size

        with open(shader_path) as f:
            self.shader = hlsl.compile(f.read())

        self.humidity_texture = Texture2D(size, size, compushady.formats.R32_FLOAT)
        self.humidity_buffer = Buffer(self.humidity_texture.size, HEAP_UPLOAD)

        self.humidity_out = Texture2D(size, size, compushady.formats.R16_FLOAT)
        self.humidity_out_buffer = Buffer(self.humidity_out.size, HEAP_READBACK)

        self.source = Texture2D(size, size, compushady.formats.R8_UINT)
        self.source_buffer = Buffer(self.source.size, HEAP_UPLOAD)

        self.noise = Texture2D(size, size, compushady.formats.R32_FLOAT)
        self.noise_buffer = Buffer(self.noise.size, HEAP_UPLOAD)

        self.target = Texture2D(size, size, compushady.formats.R8_UINT)
        self.target_buffer = Buffer(self.target.size, HEAP_READBACK)

        config = Buffer(96, HEAP_UPLOAD)
        self.config_fast = Buffer(config.size)
        config.upload(
            struct.pack(
                'fffff',
                growth_prob,
                spread_prob,
                lightning_prob,
                humidity_change,
                humidity_change_fire
            )
        )
        config.copy_to(self.config_fast)

        self.wind_config = Buffer(64, HEAP_UPLOAD)
        self.wind_buffer = Buffer(self.wind_config.size)

        self.compute = Compute(
            self.shader,
            cbv=[self.config_fast, self.wind_buffer],
            srv=[self.source, self.humidity_texture, self.noise],
            uav=[self.target, self.humidity_out]
        )

    def update_grid(self, grid: np.ndarray) -> None:
        self.source_buffer.upload(bytes(list(grid.flatten())))
        self.source_buffer.copy_to(self.source)

    def update_humidity(self, humidity: np.ndarray) -> None:
        flat = b''.join([struct.pack('f', float(x)) for x in humidity.flatten()])
        self.humidity_buffer.upload(flat)
        self.humidity_buffer.copy_to(self.humidity_texture)

    def update_noise(self, noise: np.ndarray) -> None:
        flat = b''.join([struct.pack('f', float(x)) for x in noise])
        self.noise_buffer.upload(flat)
        self.noise_buffer.copy_to(self.noise)

    def update_wind(self, wind_x: float, wind_y: float) -> None:
        self.wind_config.upload(struct.pack('ff', wind_x, wind_y))
        self.wind_config.copy_to(self.wind_buffer)

    def dispatch(self) -> None:
        self.compute.dispatch(self.size // 16, self.size // 16, 1)

    def read_results(self) -> tuple[ndarray[tuple[int, int], Any], ndarray[tuple[int, int], Any]]:
        self.target.copy_to(self.target_buffer)
        new_grid = np.array(list(self.target_buffer.readback())).reshape(self.size, self.size)

        self.humidity_out.copy_to(self.humidity_out_buffer)
        delta_humidity = np.frombuffer(
            self.humidity_out_buffer.readback(),
            dtype=np.float16
        ).reshape(self.size, self.size)

        return new_grid, delta_humidity
