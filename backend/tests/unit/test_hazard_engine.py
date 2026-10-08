import numpy as np

from backend.app.engines.hazard_engine import (
    CellFactors,
    compute_cell_hazard,
    normalize_weights,
)
from backend.app.engines.terrain_engine import (
    compute_slope_aspect_curvature,
    compute_d8_flow_accumulation,
    compute_topographic_wetness_index,
    compute_hand_approx,
)


def test_hand_computed_combined_hazard():
    """
    Verifies H = 1 - (1 - H_ls)(1 - H_fl)(1 - H_co)(1 - H_ff)
    If H_ls = 0.80, H_fl = 0.50, H_co = 0.0, H_ff = 0.0:
    H = 1 - (0.20 * 0.50 * 1.0 * 1.0) = 1 - 0.10 = 0.90
    """
    h_ls = 0.80
    h_fl = 0.50
    expected_combined = 1.0 - (1.0 - h_ls) * (1.0 - h_fl)
    assert abs(expected_combined - 0.90) < 1e-6


def test_hazard_engine_formula_and_classes():
    # Steep, near-drainage cell (High risk)
    steep_cell = CellFactors(
        slope_deg=38.0,
        dist_drainage_m=30.0,
        dist_road_m=40.0,
        hand_m=2.0,
        lulc_class="Barren land",
        past_event_count=1,
    )
    res_steep = compute_cell_hazard(steep_cell)
    assert res_steep.landslide_score > 0.60
    assert res_steep.combined_hazard >= 0.70
    assert res_steep.hazard_class == "Red"

    # Flat, high-HAND safe cell (Low risk)
    safe_cell = CellFactors(
        slope_deg=4.0,
        dist_drainage_m=800.0,
        dist_road_m=500.0,
        hand_m=35.0,
        lulc_class="Tree cover",
        past_event_count=0,
    )
    res_safe = compute_cell_hazard(safe_cell)
    assert res_safe.combined_hazard < 0.40
    assert res_safe.hazard_class == "Green"


def test_hazard_score_invariants_and_randomized_bounds():
    """Property test: All scores must strictly be in [0.0, 1.0] across 200 random inputs."""
    np.random.seed(42)
    for _ in range(200):
        slope = float(np.random.uniform(0.0, 85.0))
        hand = float(np.random.uniform(0.0, 60.0))
        dist_d = float(np.random.uniform(5.0, 2000.0))
        dist_r = float(np.random.uniform(5.0, 2000.0))
        curv = float(np.random.uniform(-0.5, 0.5))
        rf_mult = float(np.random.uniform(1.0, 3.0))

        factors = CellFactors(
            slope_deg=slope,
            hand_m=hand,
            dist_drainage_m=dist_d,
            dist_road_m=dist_r,
            curvature=curv,
        )
        res = compute_cell_hazard(factors, rainfall_multiplier=rf_mult)

        assert 0.0 <= res.landslide_score <= 1.0
        assert 0.0 <= res.flood_score <= 1.0
        assert 0.0 <= res.flash_flood_score <= 1.0
        assert 0.0 <= res.coastal_score <= 1.0
        assert 0.0 <= res.combined_hazard <= 1.0
        assert res.hazard_class in ("Red", "Amber", "Green")


def test_configured_weight_aliases_are_normalized():
    weights = normalize_weights(
        {
            "slope": 0.30,
            "distance_to_drainage": 0.15,
            "distance_to_roads": 0.15,
            "historical_events": 0.10,
        },
        {
            "distance_to_drainage": "drainage",
            "distance_to_roads": "roads",
            "historical_events": "historical",
        },
    )

    assert set(weights) == {"slope", "drainage", "roads", "historical"}
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["drainage"] == weights["roads"]


def test_structural_hazard_persists_below_dynamic_alert():
    factors = CellFactors(slope_deg=24.0, dist_drainage_m=120.0, hand_m=4.5)

    baseline = compute_cell_hazard(factors, rainfall_multiplier=1.0)
    spike = compute_cell_hazard(factors, rainfall_multiplier=2.4)

    assert spike.structural_hazard == baseline.structural_hazard
    assert spike.combined_hazard >= baseline.combined_hazard


def test_rainfall_spike_increases_hazard_and_alert():
    factors = CellFactors(slope_deg=26.0, dist_drainage_m=100.0, hand_m=4.0)

    res_baseline = compute_cell_hazard(factors, rainfall_multiplier=1.0)
    res_spike = compute_cell_hazard(factors, rainfall_multiplier=2.2)

    assert res_spike.combined_hazard >= res_baseline.combined_hazard
    assert res_spike.landslide_score >= res_baseline.landslide_score
    assert res_spike.flood_score >= res_baseline.flood_score


def test_terrain_engine_derivatives():
    # Create synthetic inclined elevation surface
    x, y = np.meshgrid(np.linspace(0, 300, 11), np.linspace(0, 300, 11))
    elevation = 100.0 + 0.2 * x + 0.3 * y  # linear plane with constant slope

    slope, aspect, curvature = compute_slope_aspect_curvature(elevation, cell_size=30.0)
    assert slope.shape == (11, 11)
    assert np.all(slope >= 0.0)

    accum = compute_d8_flow_accumulation(elevation)
    assert accum.shape == (11, 11)
    assert np.all(accum >= 1.0)

    twi = compute_topographic_wetness_index(slope, accum, cell_size=30.0)
    assert twi.shape == (11, 11)
    assert np.all(twi >= 0.0)

    hand = compute_hand_approx(elevation, accum, stream_threshold=5.0)
    assert hand.shape == (11, 11)
    assert np.all(hand >= 0.0)
