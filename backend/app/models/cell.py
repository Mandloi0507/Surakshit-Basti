from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from backend.app.database import Base


class Cell(Base):
    __tablename__ = "cells"

    id = Column(String(100), primary_key=True)  # e.g. "wayanad_cell_1024"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=False)

    # Raw terrain and proximity factors
    slope_deg = Column(Float, nullable=True)
    aspect_deg = Column(Float, nullable=True)
    curvature = Column(Float, nullable=True)
    flow_accum = Column(Float, nullable=True)
    wetness_index = Column(Float, nullable=True)
    hand_m = Column(Float, nullable=True)
    dist_drainage_m = Column(Float, nullable=True)
    dist_road_m = Column(Float, nullable=True)
    lulc_class = Column(String(50), nullable=True)
    lulc_code = Column(Integer, nullable=True)

    # Hazard scores in [0.0, 1.0]
    landslide_score = Column(Float, default=0.0, nullable=False)
    flood_score = Column(Float, default=0.0, nullable=False)
    flash_flood_score = Column(Float, default=0.0, nullable=False)
    coastal_score = Column(Float, default=0.0, nullable=False)
    structural_hazard = Column(Float, default=0.0, nullable=False, index=True)
    combined_hazard = Column(Float, default=0.0, nullable=False, index=True)
    hazard_class = Column(String(20), default="Green", nullable=False, index=True)  # Red, Amber, Green

    # Per-factor contribution breakdown for explainability
    factor_contributions_json = Column(JSON, default=dict, nullable=False)

    # Provenance
    data_origin = Column(String(30), default="CACHED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="cells")
