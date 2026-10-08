from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from backend.app.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(String(100), primary_key=True)  # e.g. "EV-2024-WYND-01"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(150), nullable=False)
    event_type = Column(String(50), default="landslide", nullable=False)
    event_date = Column(String(20), nullable=False)  # ISO-8601 date string e.g. "2024-07-30"
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(100), default="GSI / SDMA Report", nullable=False)

    # Provenance
    data_origin = Column(String(30), default="CACHED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="events")
