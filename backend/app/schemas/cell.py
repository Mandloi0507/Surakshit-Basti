from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CellBase(BaseModel):
    id: str
    district_id: str
    slope_deg: Optional[float] = None
    aspect_deg: Optional[float] = None
    curvature: Optional[float] = None
    flow_accum: Optional[float] = None
    wetness_index: Optional[float] = None
    hand_m: Optional[float] = None
    dist_drainage_m: Optional[float] = None
    dist_road_m: Optional[float] = None
    lulc_class: Optional[str] = None
    lulc_code: Optional[int] = None
    landslide_score: float = 0.0
    flood_score: float = 0.0
    flash_flood_score: float = 0.0
    coastal_score: float = 0.0
    structural_hazard: float = 0.0
    combined_hazard: float = 0.0
    hazard_class: str = "Green"
    factor_contributions_json: Dict[str, float] = Field(default_factory=dict)
    data_origin: str = "DEMO_SYNTHETIC"


class CellOut(CellBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CellGeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: CellBase
