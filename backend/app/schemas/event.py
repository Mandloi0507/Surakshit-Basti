from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class EventBase(BaseModel):
    id: str
    district_id: str
    event_name: str
    event_type: str = "landslide"
    event_date: str
    description: Optional[str] = None
    source: str = "GSI / SDMA Report"
    data_origin: str = "CACHED"


class EventOut(EventBase):
    created_at: datetime

    class Config:
        from_attributes = True


class EventGeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: Dict[str, Any]
    properties: EventBase
