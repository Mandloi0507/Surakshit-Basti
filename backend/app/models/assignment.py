from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(100), primary_key=True)  # e.g. "asgn_scen_base_hab_01"
    scenario_id = Column(String(100), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    habitation_id = Column(String(100), ForeignKey("habitations.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(100), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True, index=True)

    assigned_population = Column(Integer, default=0, nullable=False)
    distance_km = Column(Float, default=0.0, nullable=False)
    routing_method = Column(String(50), default="road_network", nullable=False)  # road_network, straight_line_fallback
    decision_rank = Column(Integer, default=1, nullable=False)

    # Explainability and solver details
    reasons_json = Column(JSON, default=list, nullable=False)
    unassigned_reason = Column(Text, nullable=True)
    solver_method = Column(String(50), default="greedy", nullable=False)  # greedy, ilp_ortools

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    scenario = relationship("Scenario", back_populates="assignments")
    habitation = relationship("Habitation", back_populates="assignments")
    site = relationship("Site", back_populates="assignments")
