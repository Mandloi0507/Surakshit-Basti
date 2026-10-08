from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CapacityNormBase(BaseModel):
    id: str
    norm_type: str
    tier: str = "temporary_shelter"
    resource_name: str
    norm_value: float
    unit: str
    source_citation: str
    is_placeholder: bool = False
    notes: Optional[str] = None


class CapacityNormOut(CapacityNormBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
