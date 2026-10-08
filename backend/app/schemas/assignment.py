from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    id: str
    scenario_id: str
    habitation_id: str
    site_id: Optional[str] = None
    assigned_population: int = 0
    distance_km: float = 0.0
    routing_method: str = "road_network"
    decision_rank: int = 1
    reasons_json: List[str] = Field(default_factory=list)
    unassigned_reason: Optional[str] = None
    solver_method: str = "greedy"


class AssignmentOut(AssignmentBase):
    created_at: datetime

    class Config:
        from_attributes = True
