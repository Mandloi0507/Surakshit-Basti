from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String

from backend.app.database import Base


class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"

    id = Column(String(100), primary_key=True)  # e.g. "rain_imerg_20261008_1200"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_time = Column(DateTime(timezone=True), nullable=False)
    valid_time = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(100), default="NASA GPM IMERG Early/Late", nullable=False)
    rainfall_mm = Column(Float, default=0.0, nullable=False)
    rainfall_grid_json = Column(JSON, default=dict, nullable=True)  # optional 2D matrix/summary

    # Provenance
    data_origin = Column(String(30), default="LIVE", nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
