from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ScenarioBase(BaseModel):
    id: str
    district_id: str
    name: str
    description: Optional[str] = None
    rainfall_multiplier: float = 1.0
    weight_overrides_json: Dict[str, Any] = Field(default_factory=dict)
    site_adjustments_json: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioOut(ScenarioBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
