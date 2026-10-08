from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from backend.app.database import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(String(50), primary_key=True)  # e.g. "wayanad"
    name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    bbox_json = Column(JSON, nullable=False)  # [minx, miny, maxx, maxy]
    geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)
    projected_crs = Column(String(20), default="EPSG:32643", nullable=False)
    grid_resolution_m = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    datasets = relationship("Dataset", back_populates="district", cascade="all, delete-orphan")
    cells = relationship("Cell", back_populates="district", cascade="all, delete-orphan")
    habitations = relationship("Habitation", back_populates="district", cascade="all, delete-orphan")
    sites = relationship("Site", back_populates="district", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="district", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="district", cascade="all, delete-orphan")
