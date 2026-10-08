from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    id: str
    user_name: str = "system"
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    before_state_json: Optional[Dict[str, Any]] = None
    after_state_json: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class AuditLogOut(AuditLogBase):
    timestamp: datetime

    class Config:
        from_attributes = True
