import numpy as np
from scipy.ndimage import gaussian_filter


def generate_cluster_map(rng: np.random.Generator,
                         size,
                         min_clusters=15,
                         max_clusters=20,
                         sigma_range=(20, 50),
                         noise_scale=25) -> np.ndarray:

    x, y = np.meshgrid(
        np.linspace(0, size, size),
        np.linspace(0, size, size)
    )
    num_clusters = rng.integers(min_clusters, max_clusters + 1)
    centers = [
        (
            rng.uniform(0, x.shape[0]),
            rng.uniform(0, y.shape[1])
        )
        for _ in range(num_clusters)
    ]
    amplitudes = [rng.uniform(0.5, 1.0) for _ in range(num_clusters)]
    sigmas = [
        (
            rng.uniform(*sigma_range),
            rng.uniform(*sigma_range)
        )
        for _ in range(num_clusters)
    ]

    noise_x = gaussian_filter(rng.random(size=x.shape), sigma=noise_scale)
    noise_y = gaussian_filter(rng.random(size=y.shape), sigma=noise_scale)

    result = np.zeros_like(x, dtype=np.float32)
    for (cx, cy), A, (sigma_x, sigma_y) in zip(centers, amplitudes, sigmas):
        wobble_x = cx + noise_x
        wobble_y = cy + noise_y
        result += A * np.exp(-(
                ((x - wobble_x)**2) / (2 * sigma_x**2)
                + ((y - wobble_y)**2) / (2 * sigma_y**2)
        ))

    result = np.clip(result / np.max(result), 0, 1)
    return result
