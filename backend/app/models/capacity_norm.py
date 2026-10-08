from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text

from backend.app.database import Base


class CapacityNorm(Base):
    __tablename__ = "capacity_norms"

    id = Column(String(100), primary_key=True)  # e.g. "norm_temp_water_sphere"
    norm_type = Column(String(50), nullable=False)  # temporary, permanent
    tier = Column(String(50), default="temporary_shelter", nullable=False)
    resource_name = Column(String(50), nullable=False)  # land, water, sanitation, road, services
    norm_value = Column(Float, nullable=False)  # e.g. 15.0 (litres/person/day) or 45.0 (sqm/household)
    unit = Column(String(50), nullable=False)
    source_citation = Column(String(255), nullable=False)  # e.g. "Sphere Handbook 2018, Water Supply Standard 2.1"
    is_placeholder = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
