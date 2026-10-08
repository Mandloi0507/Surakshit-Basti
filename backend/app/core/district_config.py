from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
from pydantic import BaseModel, Field
from backend.app.core.settings import get_settings


class HazardWeights(BaseModel):
    landslide: Dict[str, float] = Field(
        default_factory=lambda: {
            "slope": 0.30,
            "aspect": 0.10,
            "curvature": 0.10,
            "distance_to_drainage": 0.15,
            "distance_to_roads": 0.15,
            "land_cover": 0.10,
            "historical_events": 0.10,
        }
    )
    flood: Dict[str, float] = Field(
        default_factory=lambda: {
            "hand": 0.35,
            "distance_to_river": 0.25,
            "flow_accumulation": 0.20,
            "wetness_index": 0.10,
            "land_cover": 0.10,
        }
    )
    vulnerability: Dict[str, float] = Field(
        default_factory=lambda: {
            "children_under_6": 0.166,
            "elderly_60_plus": 0.166,
            "disabled_persons": 0.167,
            "female_headed_hh": 0.167,
            "kutcha_houses": 0.167,
            "distance_to_health": 0.167,
        }
    )


class ThresholdSettings(BaseModel):
    red_zone_min: float = 0.70
    amber_zone_min: float = 0.40
    immediate_urgency_min: float = 0.75
    short_term_urgency_min: float = 0.45
    rainfall_alert_trigger_mm_day: float = 100.0


class TimeFactorSettings(BaseModel):
    baseline: float = 1.0
    active_alert: float = 1.5
    recent_event: float = 1.25


class BacktestEvent(BaseModel):
    id: str
    name: str
    date: str
    hazard_type: str
    lat: float
    lon: float
    description: str


class DistrictConfig(BaseModel):
    id: str
    name: str
    state: str
    bbox: Tuple[float, float, float, float]  # (minx, miny, maxx, maxy) in WGS84
    projected_crs: str = "EPSG:32643"
    grid_resolution_m: int = 100
    hazards_active: List[str] = Field(
        default_factory=lambda: ["landslide", "flood", "flash_flood"]
    )
    weights: HazardWeights = Field(default_factory=HazardWeights)
    thresholds: ThresholdSettings = Field(default_factory=ThresholdSettings)
    time_factors: TimeFactorSettings = Field(default_factory=TimeFactorSettings)
    historical_events: List[BacktestEvent] = Field(default_factory=list)


def load_district_config(district_id: Optional[str] = None) -> DistrictConfig:
    """
    Loads district configuration from config/districts/<id>.yaml.
    Defaults to ACTIVE_DISTRICT from settings if district_id is not specified.
    """
    settings = get_settings()
    active_id = (district_id or settings.ACTIVE_DISTRICT).lower()
    config_file = settings.CONFIG_PATH / "districts" / f"{active_id}.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"District configuration file not found at: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return DistrictConfig(**data)
