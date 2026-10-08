import numpy as np
import pytest
from backend.app.engines.routing_engine import (
    LocationPoint,
    compute_distance_matrix,
    haversine_km,
    nearest_site_indices,
)


def test_haversine_accuracy():
    # Distance between Meppadi (11.55, 76.13) and Kalpetta (11.61, 76.08) in Wayanad
    dist = haversine_km(11.55, 76.13, 11.61, 76.08)
    assert 8.0 < dist < 12.0  # Approx ~8.6 km


def test_distance_matrix_computation():
    habs = [
        LocationPoint(id="h1", lat=11.55, lon=76.13),
        LocationPoint(id="h2", lat=11.65, lon=76.20),
    ]
    sites = [
        LocationPoint(id="s1", lat=11.56, lon=76.14),
        LocationPoint(id="s2", lat=11.70, lon=76.25),
        LocationPoint(id="s3", lat=11.50, lon=76.10),
    ]
    matrix_res = compute_distance_matrix(habs, sites)
    assert matrix_res.distances_km.shape == (2, 3)
    assert matrix_res.habitation_ids == ["h1", "h2"]
    assert matrix_res.site_ids == ["s1", "s2", "s3"]

    # h1 is closest to s1
    nearest = nearest_site_indices(matrix_res.distances_km)
    assert nearest[0] == 0  # Index of s1
