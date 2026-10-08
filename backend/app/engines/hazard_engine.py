from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass(frozen=True)
class CellFactors:
    slope_deg: float
    aspect_deg: float = 0.0
    curvature: float = 0.0
    flow_accum: float = 1.0
    wetness_index: float = 5.0
    hand_m: float = 15.0
    dist_drainage_m: float = 500.0
    dist_road_m: float = 500.0
    lulc_class: str = "Tree cover"
    past_event_count: int = 0


@dataclass(frozen=True)
class HazardResult:
    landslide_score: float
    flood_score: float
    flash_flood_score: float
    coastal_score: float
    combined_hazard: float
    hazard_class: str  # "Red", "Amber", "Green"
    is_alert_zone: bool
    factor_contributions: Dict[str, float]
    structural_hazard: float


def normalize_slope_landslide(slope_deg: float) -> float:
    """
    Susceptibility based on slope angle (degrees):
    - < 10 deg: very low (0.05)
    - 10-20 deg: low-moderate (0.30)
    - 20-35 deg: high (0.80)
    - 35-50 deg: very high (0.95)
    - > 50 deg: rocky cliffs / moderate-high (0.70)
    """
    if slope_deg < 10.0:
        return 0.05
    elif slope_deg < 20.0:
        return 0.10 + 0.20 * ((slope_deg - 10.0) / 10.0)
    elif slope_deg < 35.0:
        return 0.30 + 0.55 * ((slope_deg - 20.0) / 15.0)
    elif slope_deg <= 50.0:
        return 0.85 + 0.15 * ((slope_deg - 35.0) / 15.0)
    else:
        return 0.70


def normalize_hand_flood(hand_m: float) -> float:
    """
    Height Above Nearest Drainage (HAND) flood susceptibility:
    - 0 to 2m: extreme flood risk (1.0)
    - 2 to 5m: high flood risk (0.85 -> 0.60)
    - 5 to 15m: moderate risk (0.60 -> 0.10)
    - > 15m: low to zero risk (0.0)
    """
    if hand_m <= 2.0:
        return 1.0
    elif hand_m <= 5.0:
        return 0.85 - 0.25 * ((hand_m - 2.0) / 3.0)
    elif hand_m <= 15.0:
        return 0.60 - 0.50 * ((hand_m - 5.0) / 10.0)
    else:
        return max(0.0, 0.10 - 0.01 * (hand_m - 15.0))


def normalize_drainage_dist(dist_m: float) -> float:
    """Closer to natural drainage (< 50m) raises toe erosion and slope toe saturation."""
    if dist_m <= 50.0:
        return 0.90
    elif dist_m <= 200.0:
        return 0.90 - 0.40 * ((dist_m - 50.0) / 150.0)
    elif dist_m <= 500.0:
        return 0.50 - 0.35 * ((dist_m - 200.0) / 300.0)
    else:
        return 0.10


def normalize_road_dist(dist_m: float) -> float:
    """Slope cuts within 100m of roads increase slope destabilization."""
    if dist_m <= 50.0:
        return 0.85
    elif dist_m <= 150.0:
        return 0.85 - 0.45 * ((dist_m - 50.0) / 100.0)
    else:
        return 0.15


def normalize_lulc_landslide(lulc: str) -> float:
    """LULC cover factor for landslides."""
    lulc_lower = lulc.lower()
    if any(k in lulc_lower for k in ("bare", "barren", "settlement", "built-up", "cropland", "herbaceous")):
        return 0.80
    elif "shrubland" in lulc_lower or "grassland" in lulc_lower:
        return 0.50
    elif "tree" in lulc_lower or "forest" in lulc_lower:
        return 0.20
    elif "water" in lulc_lower or "wetland" in lulc_lower:
        return 0.30
    return 0.40


def normalize_lulc_flood(lulc: str) -> float:
    """LULC cover factor for floods."""
    lulc_lower = lulc.lower()
    if any(k in lulc_lower for k in ("water", "wetland", "mangrove")):
        return 0.95
    elif any(k in lulc_lower for k in ("built-up", "settlement", "cropland", "bare")):
        return 0.70
    elif "tree" in lulc_lower or "forest" in lulc_lower:
        return 0.25
    return 0.40


def normalize_aspect_landslide(aspect_deg: float) -> float:
    """Aspect susceptibility for humid Western Ghats slopes; west-facing slopes are wetter."""
    aspect = aspect_deg % 360.0
    westness = (1.0 - np.cos(np.radians(aspect - 270.0))) / 2.0
    return float(min(1.0, max(0.0, 0.25 + 0.55 * westness)))


def normalize_weights(weights: Dict[str, float], aliases: Dict[str, str]) -> Dict[str, float]:
    """Canonicalise configured weights and renormalise positive values to sum to one."""
    canonical: Dict[str, float] = {}
    for key, value in weights.items():
        canonical_key = aliases.get(key, key)
        canonical[canonical_key] = canonical.get(canonical_key, 0.0) + max(0.0, float(value))

    total = sum(canonical.values())
    if total <= 0.0:
        raise ValueError("Hazard weights must contain at least one positive value")
    return {key: value / total for key, value in canonical.items()}


def compute_cell_hazard(
    factors: CellFactors,
    landslide_weights: Optional[Dict[str, float]] = None,
    flood_weights: Optional[Dict[str, float]] = None,
    rainfall_multiplier: float = 1.0,
    rainfall_mm: float = 0.0,
    rainfall_alert_trigger_mm: float = 100.0,
    threshold_red: float = 0.70,
    threshold_amber: float = 0.40,
    coastal_score: float = 0.0,
) -> HazardResult:
    """
    Computes individual and combined multi-hazard scores for a single cell.
    Formula: H = 1 - (1 - H_ls)(1 - H_fl)(1 - H_co)(1 - H_ff)
    """
    # 1. Normalized Factor Scores
    f_slope = normalize_slope_landslide(factors.slope_deg)
    f_drainage = normalize_drainage_dist(factors.dist_drainage_m)
    f_road = normalize_road_dist(factors.dist_road_m)
    f_aspect = normalize_aspect_landslide(factors.aspect_deg)
    f_curv = min(1.0, max(0.0, 0.5 - factors.curvature * 2.0))
    f_lulc_ls = normalize_lulc_landslide(factors.lulc_class)
    f_past = min(1.0, factors.past_event_count * 0.4)

    # Landslide weighted overlay
    default_landslide_weights = {
        "slope": 0.35,
        "aspect": 0.05,
        "drainage": 0.15,
        "roads": 0.15,
        "curvature": 0.10,
        "land_cover": 0.15,
        "historical": 0.10,
    }
    ls_aliases = {
        "distance_to_drainage": "drainage",
        "distance_to_roads": "roads",
        "historical_events": "historical",
    }
    ls_w = normalize_weights(landslide_weights or default_landslide_weights, ls_aliases)
    h_ls_struct = (
        ls_w.get("slope", 0.0) * f_slope
        + ls_w.get("aspect", 0.0) * f_aspect
        + ls_w.get("drainage", 0.0) * f_drainage
        + ls_w.get("roads", 0.0) * f_road
        + ls_w.get("curvature", 0.0) * f_curv
        + ls_w.get("land_cover", 0.0) * f_lulc_ls
        + ls_w.get("historical", 0.0) * f_past
    )
    h_ls_struct = min(1.0, max(0.0, h_ls_struct))

    # 2. Flood Hazard
    f_hand = normalize_hand_flood(factors.hand_m)
    f_twi = min(1.0, max(0.0, (factors.wetness_index - 3.0) / 12.0))
    f_accum = min(1.0, np.log10(max(1.0, factors.flow_accum)) / 5.0)
    f_lulc_fl = normalize_lulc_flood(factors.lulc_class)

    default_flood_weights = {
        "hand": 0.40,
        "river_distance": 0.20,
        "wetness": 0.20,
        "flow_accum": 0.20,
        "land_cover": 0.20,
    }
    fl_aliases = {
        "distance_to_river": "river_distance",
        "flow_accumulation": "flow_accum",
        "wetness_index": "wetness",
    }
    fl_w = normalize_weights(flood_weights or default_flood_weights, fl_aliases)
    h_fl_struct = (
        fl_w.get("hand", 0.0) * f_hand
        + fl_w.get("river_distance", 0.0) * f_drainage
        + fl_w.get("wetness", 0.0) * f_twi
        + fl_w.get("flow_accum", 0.0) * f_accum
        + fl_w.get("land_cover", 0.0) * f_lulc_fl
    )
    h_fl_struct = min(1.0, max(0.0, h_fl_struct))

    # 3. Dynamic Multiplier & Flash Flood
    effective_multiplier = max(1.0, rainfall_multiplier)
    if rainfall_mm > 0:
        ratio = rainfall_mm / max(1.0, rainfall_alert_trigger_mm)
        effective_multiplier = max(effective_multiplier, min(2.5, ratio))

    h_ls_dyn = min(1.0, h_ls_struct * effective_multiplier)
    h_fl_dyn = min(1.0, h_fl_struct * effective_multiplier)

    # Flash flood trigger on steep slopes with high rainfall multiplier
    is_steep = factors.slope_deg > 15.0
    h_ff = min(1.0, 0.40 * (effective_multiplier - 1.0) * (1.2 if is_steep else 0.5)) if effective_multiplier > 1.0 else 0.0

    # 4. Multi-Hazard Combination
    h_co = min(1.0, max(0.0, coastal_score))
    combined_structural = 1.0 - (1.0 - h_ls_struct) * (1.0 - h_fl_struct) * (1.0 - h_co)
    combined_dynamic = 1.0 - (1.0 - h_ls_dyn) * (1.0 - h_fl_dyn) * (1.0 - h_co) * (1.0 - h_ff)

    combined_dynamic = min(1.0, max(0.0, float(combined_dynamic)))
    combined_structural = min(1.0, max(0.0, float(combined_structural)))

    # Classification
    if combined_dynamic >= threshold_red:
        h_class = "Red"
    elif combined_dynamic >= threshold_amber:
        h_class = "Amber"
    else:
        h_class = "Green"

    is_alert_zone = (combined_dynamic >= threshold_red) and (combined_structural < threshold_red)

    # Factor contributions (percentage breakdown of primary drivers)
    contributions = {
        "slope": round(float(f_slope * ls_w.get("slope", 0.0)), 4),
        "aspect": round(float(f_aspect * ls_w.get("aspect", 0.0)), 4),
        "hand_elevation": round(float(f_hand * fl_w.get("hand", 0.0)), 4),
        "drainage_proximity": round(float(f_drainage * (ls_w.get("drainage", 0.0) + fl_w.get("river_distance", 0.0))), 4),
        "road_proximity": round(float(f_road * ls_w.get("roads", 0.0)), 4),
        "wetness_flow": round(float((f_twi * fl_w.get("wetness", 0.0)) + (f_accum * fl_w.get("flow_accum", 0.0))), 4),
        "land_cover": round(float((f_lulc_ls * ls_w.get("land_cover", 0.0)) + (f_lulc_fl * fl_w.get("land_cover", 0.0))), 4),
        "historical_events": round(float(f_past * ls_w.get("historical", 0.0)), 4),
        "rainfall_trigger": round(float(max(0.0, (effective_multiplier - 1.0) * 0.3)), 4),
    }

    return HazardResult(
        landslide_score=round(float(h_ls_dyn), 4),
        flood_score=round(float(h_fl_dyn), 4),
        flash_flood_score=round(float(h_ff), 4),
        coastal_score=round(float(h_co), 4),
        combined_hazard=round(float(combined_dynamic), 4),
        hazard_class=h_class,
        is_alert_zone=is_alert_zone,
        factor_contributions=contributions,
        structural_hazard=round(float(combined_structural), 4),
    )

