from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(100), primary_key=True)  # e.g. "scen_baseline", "scen_monsoon_spike"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # What-if simulation parameters
    rainfall_multiplier = Column(Float, default=1.0, nullable=False)
    weight_overrides_json = Column(JSON, default=dict, nullable=False)
    site_adjustments_json = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="scenarios")
    assignments = relationship("Assignment", back_populates="scenario", cascade="all, delete-orphan")
