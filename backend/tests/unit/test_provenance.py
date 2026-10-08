from datetime import datetime, timezone, timedelta
from backend.app.core.provenance import (
    DataOrigin,
    FreshnessStatus,
    combine_origins,
    compute_freshness,
    create_provenance,
)


def test_provenance_creation():
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    retrieved = now - timedelta(hours=2)

    prov = create_provenance(
        source="NASA GPM IMERG",
        origin=DataOrigin.LIVE,
        retrieved_at=retrieved,
        max_age_seconds=86400,
        now=now,
    )

    assert prov.data_origin == DataOrigin.LIVE
    assert prov.source == "NASA GPM IMERG"
    assert prov.age_seconds == 7200
    assert prov.freshness == FreshnessStatus.FRESH


def test_provenance_stale_detection():
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    retrieved = now - timedelta(days=2)

    prov = create_provenance(
        source="Test Source",
        origin=DataOrigin.CACHED,
        retrieved_at=retrieved,
        max_age_seconds=86400,
        now=now,
    )

    assert prov.freshness == FreshnessStatus.STALE


def test_combine_origins_hierarchy():
    # Weakest origin wins
    assert combine_origins([DataOrigin.LIVE, DataOrigin.LIVE]) == DataOrigin.LIVE
    assert combine_origins([DataOrigin.LIVE, DataOrigin.CACHED]) == DataOrigin.CACHED
    assert combine_origins([DataOrigin.LIVE, DataOrigin.DEMO_SYNTHETIC]) == DataOrigin.DEMO_SYNTHETIC
    assert combine_origins([DataOrigin.CACHED, DataOrigin.UNAVAILABLE]) == DataOrigin.UNAVAILABLE
    assert combine_origins([]) == DataOrigin.LIVE
