from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HabitationBase(BaseModel):
    id: str
    district_id: str
    name: str
    population: int = 0
    households: int = 0
    vuln_children_u6: float = 0.0
    vuln_elderly_60p: float = 0.0
    vuln_disabled: float = 0.0
    vuln_female_head: float = 0.0
    vuln_kutcha: float = 0.0
    vuln_dist_health_m: float = 0.0
    vulnerability_index: float = 0.0
    hazard_score: float = 0.0
    structural_hazard: float = 0.0
    time_factor: float = 1.0
    raw_urgency_score: float = 0.0
    urgency_score: float = 0.0
    bucket: str = "NONE"
    vulnerability_breakdown_json: Dict[str, Any] = Field(default_factory=dict)
    urgency_breakdown_json: Dict[str, Any] = Field(default_factory=dict)
    assigned_site_id: Optional[str] = None
    unassigned_reason: Optional[str] = None
    decision_reasons_json: Dict[str, Any] = Field(default_factory=dict)
    data_origin: str = "DEMO_SYNTHETIC"


class HabitationOut(HabitationBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HabitationGeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: HabitationBase
