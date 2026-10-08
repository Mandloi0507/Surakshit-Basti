from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(100), primary_key=True)  # e.g. "wayanad_dem_glo30"
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    license = Column(String(100), nullable=True)
    access_date = Column(String(20), nullable=True)
    data_origin = Column(String(30), default="CACHED", nullable=False)
    checksum = Column(String(128), nullable=True)
    processing_status = Column(String(50), default="processed", nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    district = relationship("District", back_populates="datasets")
    ingestion_runs = relationship("IngestionRun", back_populates="dataset", cascade="all, delete-orphan")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(100), primary_key=True)
    dataset_id = Column(String(100), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    district_id = Column(String(50), ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    data_origin = Column(String(30), nullable=False)
    status = Column(String(30), default="COMPLETED", nullable=False)  # COMPLETED, FAILED, RUNNING
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    row_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    dataset = relationship("Dataset", back_populates="ingestion_runs")
