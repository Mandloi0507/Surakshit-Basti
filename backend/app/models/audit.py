from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, JSON, String, Text

from backend.app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(100), primary_key=True)  # e.g. "audit_20261008_001"
    user_name = Column(String(100), default="system", nullable=False)
    action = Column(String(100), nullable=False)  # e.g. "scenario_created", "threshold_adjusted", "officer_override"
    resource_type = Column(String(50), nullable=False)  # scenario, habitation, site, assignment
    resource_id = Column(String(100), nullable=True)
    before_state_json = Column(JSON, default=dict, nullable=True)
    after_state_json = Column(JSON, default=dict, nullable=True)
    notes = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
