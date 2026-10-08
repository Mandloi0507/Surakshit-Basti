from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataOrigin(str, Enum):
    LIVE = "LIVE"
    CACHED = "CACHED"
    DEMO_SYNTHETIC = "DEMO_SYNTHETIC"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


class ProvenanceEnvelope(BaseModel):
    data_origin: DataOrigin
    source: str
    retrieved_at: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    age_seconds: Optional[int] = None
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN
    license: Optional[str] = None
    notes: Optional[str] = None


def compute_freshness(
    retrieved_at: Optional[datetime],
    max_age_seconds: int = 86400,
    now: Optional[datetime] = None,
) -> FreshnessStatus:
    """Computes freshness status based on age threshold."""
    if retrieved_at is None:
        return FreshnessStatus.UNKNOWN

    current_time = now or datetime.now(timezone.utc)
    # Ensure retrieved_at has timezone info
    if retrieved_at.tzinfo is None:
        retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)

    age = int((current_time - retrieved_at).total_seconds())
    if age < 0:
        return FreshnessStatus.FRESH
    return FreshnessStatus.FRESH if age <= max_age_seconds else FreshnessStatus.STALE


def combine_origins(origins: List[DataOrigin]) -> DataOrigin:
    """
    Combines origins: output inherits the weakest origin of its inputs.
    Hierarchy: UNAVAILABLE > DEMO_SYNTHETIC > SIMULATED > CACHED > LIVE
    """
    if not origins:
        return DataOrigin.LIVE

    hierarchy = [
        DataOrigin.UNAVAILABLE,
        DataOrigin.DEMO_SYNTHETIC,
        DataOrigin.SIMULATED,
        DataOrigin.CACHED,
        DataOrigin.LIVE,
    ]

    for origin in hierarchy:
        if origin in origins:
            return origin

    return DataOrigin.LIVE


def create_provenance(
    source: str,
    origin: DataOrigin,
    retrieved_at: Optional[datetime] = None,
    valid_time: Optional[datetime] = None,
    max_age_seconds: int = 86400,
    license: Optional[str] = None,
    notes: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ProvenanceEnvelope:
    """Factory helper to build a ProvenanceEnvelope."""
    current_time = now or datetime.now(timezone.utc)
    age_seconds: Optional[int] = None

    if retrieved_at:
        if retrieved_at.tzinfo is None:
            retrieved_at = retrieved_at.replace(tzinfo=timezone.utc)
        age_seconds = max(0, int((current_time - retrieved_at).total_seconds()))

    freshness = (
        FreshnessStatus.UNAVAILABLE
        if origin == DataOrigin.UNAVAILABLE
        else compute_freshness(retrieved_at, max_age_seconds=max_age_seconds, now=current_time)
    )

    return ProvenanceEnvelope(
        data_origin=origin,
        source=source,
        retrieved_at=retrieved_at,
        valid_time=valid_time,
        age_seconds=age_seconds,
        freshness=freshness,
        license=license,
        notes=notes,
    )
