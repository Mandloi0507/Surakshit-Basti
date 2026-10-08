# 0001. Foundation Infrastructure & Minimal Dependencies (Alembic, Pytest, HTTPX)

**Status:** Accepted  
**Date:** 2026-10-08  
**Tag:** `[ENGINEERING DECISION]`

---

## Context
Phase 1 of Surakshit Basti establishes the foundational core architecture:
1. Pydantic-based configuration and settings (`backend/app/core/settings.py`).
2. Structured contextual logging without secrets leakage (`backend/app/core/logging.py`).
3. Provenance envelope, freshness calculation, and `DataOrigin` enum (`backend/app/core/provenance.py`).
4. GIS coordinate reference system assertion utility `assert_same_crs` (`backend/app/core/gis_utils.py`).
5. District configuration model and YAML loader (`backend/app/core/district_config.py`).
6. Skeleton `/api/v1/status` endpoint.

To guarantee schema migrations without manual DDL or `create_all()`, and to establish an automated test suite matching the PRD/AGENTS specifications, two minimal dependency additions are required:
- `alembic`: Standard SQLAlchemy migration management tool.
- `pytest` & `httpx`: Automated testing runner and HTTP client required for FastAPI's `TestClient`.

## Decision
1. Install `alembic`, `pytest`, and `httpx` into `backend/.venv`.
2. Pin exact versions into `backend/requirements.txt`.
3. Initialize Alembic configured to read settings from `backend.app.core.settings` and target the `surakshit_basti` database, ignoring PostGIS spatial tables in autogenerate (`spatial_ref_sys`, `geometry_columns`, `geography_columns`).
4. Establish test directory layout `backend/tests/unit/`, `backend/tests/integration/`, `backend/tests/api/` with basic test suites for settings, provenance, GIS CRS assertions, and API health.

## Compatibility Check
- Python: 3.11.9
- SQLAlchemy: 2.1.3
- Pydantic: 2.13.5
- GeoPandas: 1.2.0 / Shapely: 2.1.2
All additions are pure Python or widely standard wheels fully compatible with Python 3.11.9 on Windows.

## Rollback Plan
If any conflict or baseline checklist regression occurs:
1. `pip uninstall alembic pytest httpx -y`
2. Revert `backend/requirements.txt` to the exact previous pin list.
3. Remove `backend/migrations/` and `backend/alembic.ini`.
