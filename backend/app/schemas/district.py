from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class DistrictBase(BaseModel):
    id: str
    name: str
    state: str
    bbox_json: Tuple[float, float, float, float]
    projected_crs: str = "EPSG:32643"
    grid_resolution_m: int = 100


class DistrictCreate(DistrictBase):
    pass


class DistrictOut(DistrictBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
