from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from backend.app.database import Base


class Habitation(Base):
    __tablename__ = "habitations"

    id = Column(String(100), primary_key=True)  # e.g. "wayanad_hab_01"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)

    # Demographics
    population = Column(Integer, default=0, nullable=False)
    households = Column(Integer, default=0, nullable=False)

    # 6 Vulnerability Proxies (ratios [0.0, 1.0] and metric distance)
    vuln_children_u6 = Column(Float, default=0.0, nullable=False)
    vuln_elderly_60p = Column(Float, default=0.0, nullable=False)
    vuln_disabled = Column(Float, default=0.0, nullable=False)
    vuln_female_head = Column(Float, default=0.0, nullable=False)
    vuln_kutcha = Column(Float, default=0.0, nullable=False)
    vuln_dist_health_m = Column(Float, default=0.0, nullable=False)

    # Computed Index & Scores
    vulnerability_index = Column(Float, default=0.0, nullable=False)
    hazard_score = Column(Float, default=0.0, nullable=False)
    structural_hazard = Column(Float, default=0.0, nullable=False)
    time_factor = Column(Float, default=1.0, nullable=False)
    raw_urgency_score = Column(Float, default=0.0, nullable=False)
    urgency_score = Column(Float, default=0.0, nullable=False, index=True)
    bucket = Column(String(30), default="NONE", nullable=False, index=True)  # Immediate, Short-term, Medium-term, NONE
    vulnerability_breakdown_json = Column(JSON, default=dict, nullable=False)
    urgency_breakdown_json = Column(JSON, default=dict, nullable=False)

    # Assignment Snapshot
    assigned_site_id = Column(String(100), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)
    unassigned_reason = Column(Text, nullable=True)
    decision_reasons_json = Column(JSON, default=dict, nullable=False)

    # Provenance
    data_origin = Column(String(30), default="DEMO_SYNTHETIC", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="habitations")
    assigned_site = relationship("Site", back_populates="assigned_habitations")
    assignments = relationship("Assignment", back_populates="habitation", cascade="all, delete-orphan")
