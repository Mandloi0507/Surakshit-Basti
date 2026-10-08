import pytest
from backend.app.engines.capacity_engine import (
    CapacityNorms,
    CapacityResult,
    ScreeningThresholds,
    SiteResourceInputs,
    SiteScreeningInput,
    compute_capacity,
    invariant_capacity_is_min,
    screen_site,
    tier_from_capacity,
)


def test_capacity_is_minimum_of_all_five_resources():
    norms = CapacityNorms(
        land_sqm_per_person=10.0,
        water_litres_per_person_day=20.0,
        sanitation_persons_per_toilet=25.0,
        road_persons_per_m_width=50.0,
        service_person_capacity=500,
        usable_land_fraction=1.0,
    )
    # Land: 5000 / 10 = 500
    # Water: 8000 / 20 = 400
    # Sanitation: 10 * 25 = 250 (Limiting!)
    # Road: 10 * 50 = 500
    # Service: 500
    inputs = SiteResourceInputs(
        area_sqm=5000.0,
        water_litres_day=8000.0,
        toilets=10,
        road_width_m=10.0,
        service_capacity=500,
    )
    res: CapacityResult = compute_capacity(inputs, norms)

    assert res.final_capacity == 250
    assert res.limiting_factor == "sanitation"
    assert res.cap_land == 500
    assert res.cap_water == 400
    assert res.cap_sanitation == 250
    assert invariant_capacity_is_min([res]) is True


def test_site_screening_eligibility():
    eligible_site = SiteScreeningInput(
        slope_deg=8.5,
        hazard_score=0.15,
        land_cover="barren grassland",
        dist_road_m=200.0,
        dist_water_m=400.0,
        protected_or_wetland=False,
    )
    res = screen_site(eligible_site)
    assert res.is_eligible is True
    assert res.confidence_level == "high"
    assert len(res.rejections) == 0

    steep_hazard_site = SiteScreeningInput(
        slope_deg=22.0,  # Exceeds 15 deg
        hazard_score=0.65,  # Exceeds 0.40
        land_cover="dense forest",
        dist_road_m=1500.0,
        dist_water_m=2000.0,
        protected_or_wetland=True,
    )
    res_ineligible = screen_site(steep_hazard_site)
    assert res_ineligible.is_eligible is False
    assert len(res_ineligible.rejections) >= 3


def test_tier_from_capacity():
    assert tier_from_capacity(500, temporary_threshold=250) == "permanent_site"
    assert tier_from_capacity(100, temporary_threshold=250) == "temporary_shelter"
