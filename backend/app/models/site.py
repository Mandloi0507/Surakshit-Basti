from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from backend.app.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(String(100), primary_key=True)  # e.g. "wayanad_site_01"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    tier = Column(String(50), default="temporary_shelter", nullable=False)  # temporary_shelter, permanent_site

    # Physical screening attributes
    area_sqm = Column(Float, default=0.0, nullable=False)
    slope_deg = Column(Float, default=0.0, nullable=False)
    dist_road_m = Column(Float, default=0.0, nullable=False)
    dist_water_m = Column(Float, default=0.0, nullable=False)

    # Multi-resource capacity components (in persons/households)
    cap_land = Column(Integer, default=0, nullable=False)
    cap_water = Column(Integer, default=0, nullable=False)
    cap_sanitation = Column(Integer, default=0, nullable=False)
    cap_road = Column(Integer, default=0, nullable=False)
    cap_services = Column(Integer, default=0, nullable=False)

    # Aggregate capacity and limiting resource
    final_capacity = Column(Integer, default=0, nullable=False, index=True)
    limiting_factor = Column(String(50), default="land", nullable=False)
    allocated_population = Column(Integer, default=0, nullable=False)
    remaining_capacity = Column(Integer, default=0, nullable=False)

    # Screening & Audit
    confidence_level = Column(String(20), default="medium", nullable=False)  # low, medium, high
    screening_reasons_json = Column(JSON, default=list, nullable=False)

    # Provenance
    data_origin = Column(String(30), default="DEMO_SYNTHETIC", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="sites")
    assigned_habitations = relationship("Habitation", back_populates="assigned_site")
    assignments = relationship("Assignment", back_populates="site", cascade="all, delete-orphan")
