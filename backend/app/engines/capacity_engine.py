from dataclasses import dataclass
from math import floor
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class CapacityNorms:
    """Capacity norms; all capacity components are returned as persons."""

    land_sqm_per_person: float
    water_litres_per_person_day: float
    sanitation_persons_per_toilet: float
    road_persons_per_m_width: float
    service_person_capacity: int
    usable_land_fraction: float = 0.65


@dataclass(frozen=True)
class SiteResourceInputs:
    area_sqm: float
    water_litres_day: float
    toilets: int
    road_width_m: float
    service_capacity: int | None = None


@dataclass(frozen=True)
class CapacityResult:
    cap_land: int
    cap_water: int
    cap_sanitation: int
    cap_road: int
    cap_services: int
    final_capacity: int
    limiting_factor: str
    components: Dict[str, int]


@dataclass(frozen=True)
class SiteScreeningInput:
    slope_deg: float
    hazard_score: float
    land_cover: str
    dist_road_m: float
    dist_water_m: float
    protected_or_wetland: bool = False


@dataclass(frozen=True)
class ScreeningThresholds:
    max_slope_deg: float = 15.0
    max_hazard_score: float = 0.40
    max_dist_road_m: float = 1000.0
    max_dist_water_m: float = 1500.0
    allowed_land_covers: tuple[str, ...] = ("barren", "bare", "scrub", "grassland", "herbaceous")


@dataclass(frozen=True)
class ScreeningResult:
    is_eligible: bool
    reasons: List[str]
    rejections: List[str]
    confidence_level: str


def compute_capacity(inputs: SiteResourceInputs, norms: CapacityNorms) -> CapacityResult:
    """Compute C_j = min(C_land, C_water, C_sanitation, C_road, C_services)."""
    usable_area_sqm = max(0.0, inputs.area_sqm) * max(0.0, min(1.0, norms.usable_land_fraction))
    cap_land = floor(usable_area_sqm / max(1.0, norms.land_sqm_per_person))
    cap_water = floor(max(0.0, inputs.water_litres_day) / max(1.0, norms.water_litres_per_person_day))
    cap_sanitation = floor(max(0, inputs.toilets) * max(1.0, norms.sanitation_persons_per_toilet))
    cap_road = floor(max(0.0, inputs.road_width_m) * max(1.0, norms.road_persons_per_m_width))
    cap_services = max(0, int(inputs.service_capacity if inputs.service_capacity is not None else norms.service_person_capacity))
    components = {
        "land": cap_land,
        "water": cap_water,
        "sanitation": cap_sanitation,
        "road": cap_road,
        "services": cap_services,
    }
    limiting_factor = min(components, key=lambda key: (components[key], key))
    return CapacityResult(
        cap_land=cap_land,
        cap_water=cap_water,
        cap_sanitation=cap_sanitation,
        cap_road=cap_road,
        cap_services=cap_services,
        final_capacity=components[limiting_factor],
        limiting_factor=limiting_factor,
        components=components,
    )


def screen_site(
    inputs: SiteScreeningInput,
    thresholds: ScreeningThresholds = ScreeningThresholds(),
) -> ScreeningResult:
    """Screen a candidate site against PRD Phase 6 GIS rules."""
    reasons: List[str] = []
    rejections: List[str] = []
    land_cover = inputs.land_cover.lower()

    if inputs.hazard_score < thresholds.max_hazard_score:
        reasons.append("Outside Red/Amber hazard threshold")
    else:
        rejections.append("Inside Red/Amber hazard threshold")

    if inputs.slope_deg < thresholds.max_slope_deg:
        reasons.append("Slope below screening threshold")
    else:
        rejections.append("Slope exceeds screening threshold")

    if any(token in land_cover for token in thresholds.allowed_land_covers):
        reasons.append("Land cover is compatible with open-site screening")
    else:
        rejections.append("Land cover is not compatible with open-site screening")

    if inputs.dist_road_m <= thresholds.max_dist_road_m:
        reasons.append("Within road access threshold")
    else:
        rejections.append("Too far from all-weather road proxy")

    if inputs.dist_water_m <= thresholds.max_dist_water_m:
        reasons.append("Within water access threshold")
    else:
        rejections.append("Too far from water source proxy")

    if not inputs.protected_or_wetland:
        reasons.append("Not flagged as protected forest or wetland")
    else:
        rejections.append("Protected forest or wetland flag present")

    confidence_level = "high" if not rejections else ("medium" if len(rejections) <= 2 else "low")
    return ScreeningResult(
        is_eligible=not rejections,
        reasons=reasons,
        rejections=rejections,
        confidence_level=confidence_level,
    )


def tier_from_capacity(final_capacity: int, temporary_threshold: int = 250) -> str:
    """Assign a simple MVP site tier from computed capacity."""
    return "permanent_site" if final_capacity >= temporary_threshold else "temporary_shelter"


def invariant_capacity_is_min(results: Iterable[CapacityResult]) -> bool:
    """Return True when every final capacity equals the minimum component capacity."""
    return all(result.final_capacity == min(result.components.values()) for result in results)
