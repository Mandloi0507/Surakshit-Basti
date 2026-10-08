from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SiteBase(BaseModel):
    id: str
    district_id: str
    name: str
    tier: str = "temporary_shelter"
    area_sqm: float = 0.0
    slope_deg: float = 0.0
    dist_road_m: float = 0.0
    dist_water_m: float = 0.0
    cap_land: int = 0
    cap_water: int = 0
    cap_sanitation: int = 0
    cap_road: int = 0
    cap_services: int = 0
    final_capacity: int = 0
    limiting_factor: str = "land"
    allocated_population: int = 0
    remaining_capacity: int = 0
    confidence_level: str = "medium"
    screening_reasons_json: List[str] = Field(default_factory=list)
    data_origin: str = "DEMO_SYNTHETIC"


class SiteOut(SiteBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SiteGeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: SiteBase
