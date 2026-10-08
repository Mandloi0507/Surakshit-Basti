"""
Routing engine: computes distance matrices between habitations and candidate sites.
Uses haversine (great-circle) distance as primary; road-network routing is
[OPTIONAL FUTURE ENHANCEMENT] pending OSM extract for the pilot district.
"""
from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt
from typing import Dict, List, Tuple

import numpy as np


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two WGS84 points."""
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2.0) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(max(0.0, 1.0 - a)))


@dataclass(frozen=True)
class LocationPoint:
    """A named location with WGS84 coordinates."""
    id: str
    lat: float
    lon: float


@dataclass(frozen=True)
class DistanceMatrixResult:
    """Distance matrix between habitations and sites."""
    habitation_ids: List[str]
    site_ids: List[str]
    distances_km: np.ndarray  # shape (n_habitations, n_sites)
    routing_method: str  # "straight_line_fallback" or "road_network"


def compute_distance_matrix(
    habitations: List[LocationPoint],
    sites: List[LocationPoint],
) -> DistanceMatrixResult:
    """
    Compute haversine distance matrix between all habitations and sites.
    Returns distances in km. Shape: (len(habitations), len(sites)).
    """
    n_hab = len(habitations)
    n_site = len(sites)
    distances = np.zeros((n_hab, n_site), dtype=np.float64)

    for i, hab in enumerate(habitations):
        for j, site in enumerate(sites):
            distances[i, j] = haversine_km(hab.lat, hab.lon, site.lat, site.lon)

    return DistanceMatrixResult(
        habitation_ids=[h.id for h in habitations],
        site_ids=[s.id for s in sites],
        distances_km=distances,
        routing_method="straight_line_fallback",
    )


def nearest_site_indices(
    distances_km: np.ndarray,
    eligible_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    For each habitation (row), return the index of the nearest eligible site.
    eligible_mask: boolean (n_hab, n_site) — True if assignment is allowed.
    Returns array of shape (n_hab,) with site indices (-1 if no eligible site).
    """
    n_hab, n_site = distances_km.shape
    if eligible_mask is None:
        eligible_mask = np.ones((n_hab, n_site), dtype=bool)

    result = np.full(n_hab, -1, dtype=np.int64)
    masked_dist = np.where(eligible_mask, distances_km, np.inf)

    for i in range(n_hab):
        row = masked_dist[i]
        if np.all(np.isinf(row)):
            result[i] = -1
        else:
            result[i] = int(np.argmin(row))

    return result
