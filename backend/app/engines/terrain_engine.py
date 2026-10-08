import numpy as np
from scipy import ndimage
from typing import Dict, Tuple


def compute_slope_aspect_curvature(
    elevation: np.ndarray,
    cell_size: float = 30.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes terrain slope (degrees), aspect (degrees 0-360), and curvature (Laplacian).
    Uses 2nd-order central difference gradient operators.
    """
    # Compute gradients (dz/dy, dz/dx)
    dz_dy, dz_dx = np.gradient(elevation, cell_size)

    # Slope in degrees: 0 to 90 deg
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_deg = np.degrees(slope_rad)

    # Aspect in degrees: 0 to 360 deg clockwise from North
    aspect_rad = np.arctan2(-dz_dx, dz_dy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = np.where(aspect_deg < 0, 360.0 + aspect_deg, aspect_deg)

    # Curvature via Laplacian
    d2z_dy2, _ = np.gradient(dz_dy, cell_size)
    _, d2z_dx2 = np.gradient(dz_dx, cell_size)
    curvature = d2z_dx2 + d2z_dy2

    return slope_deg, aspect_deg, curvature


def compute_d8_flow_accumulation(elevation: np.ndarray) -> np.ndarray:
    """
    Computes single-direction (D8) steepest descent flow accumulation.
    Returns flow accumulation count per cell (>= 1).
    """
    rows, cols = elevation.shape
    accum = np.ones((rows, cols), dtype=np.float64)

    # Sort cell coordinates by elevation descending (highest to lowest)
    flat_indices = np.argsort(-elevation.ravel())

    # 8 neighbor offsets: (dy, dx, distance_scale)
    sqrt2 = np.sqrt(2.0)
    neighbors = [
        (-1, -1, sqrt2), (-1, 0, 1.0), (-1, 1, sqrt2),
        (0, -1, 1.0),                  (0, 1, 1.0),
        (1, -1, sqrt2),  (1, 0, 1.0),  (1, 1, sqrt2),
    ]

    for idx in flat_indices:
        r = idx // cols
        c = idx % cols
        z = elevation[r, c]

        max_slope = 0.0
        target_r, target_c = -1, -1

        for dr, dc, dist in neighbors:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nz = elevation[nr, nc]
                drop = (z - nz) / dist
                if drop > max_slope:
                    max_slope = drop
                    target_r, target_c = nr, nc

        if target_r != -1 and target_c != -1:
            accum[target_r, target_c] += accum[r, c]

    return accum


def compute_topographic_wetness_index(
    slope_deg: np.ndarray,
    flow_accum: np.ndarray,
    cell_size: float = 30.0,
) -> np.ndarray:
    """
    Computes Topographic Wetness Index (TWI):
    TWI = ln( (a * cell_size) / (tan(beta) + eps) )
    """
    slope_rad = np.radians(np.clip(slope_deg, 0.1, 89.9))
    tan_slope = np.tan(slope_rad)
    specific_catchment_area = flow_accum * cell_size

    twi = np.log((specific_catchment_area + 1.0) / (tan_slope + 0.001))
    return np.clip(twi, 0.0, 25.0)


def compute_hand_approx(
    elevation: np.ndarray,
    flow_accum: np.ndarray,
    stream_threshold: float = 100.0,
) -> np.ndarray:
    """
    Computes Height Above Nearest Drainage (HAND):
    Identifies drainage network where flow_accum >= stream_threshold,
    then computes elevation difference to nearest stream cell.
    """
    stream_mask = flow_accum >= stream_threshold
    if not np.any(stream_mask):
        # Fallback if no stream reaches threshold
        stream_mask = flow_accum >= np.percentile(flow_accum, 95)

    stream_elevation = np.where(stream_mask, elevation, np.nan)

    # Nearest neighbor interpolation to spread stream elevation to all cells
    indices = ndimage.distance_transform_edt(
        ~stream_mask, return_distances=False, return_indices=True
    )
    nearest_stream_elev = elevation[indices[0], indices[1]]

    hand = np.maximum(0.0, elevation - nearest_stream_elev)
    return hand
