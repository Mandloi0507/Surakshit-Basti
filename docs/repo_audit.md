# Repository Audit & Baseline Report — Surakshit Basti

**Date:** 2026-10-08  
**Phase:** Phase 0 — Repository Audit & Baseline  
**Project:** Surakshit Basti — Proactive Relocation Intelligence for Disaster-Prone Habitations (SIH26191, MHA / NDRF)  
**Status:** Completed — Baseline Green

---

## 1. Executive Summary

A comprehensive, non-destructive audit of the Surakshit Basti repository was conducted. The underlying infrastructure (FastAPI backend, PostgreSQL 17 + PostGIS 3.6.2 database, and React 19 + TypeScript + Vite + MapLibre frontend) is verified, healthy, and operational. No modifications have been made to existing code or dependencies during this audit.

---

## 2. Baseline Verification Checklist

| Item | Expected | Actual Result | Status |
|---|---|---|---|
| **Python Virtual Environment** | `backend/.venv` (Python 3.11.9) | Python 3.11.9 in `backend/.venv` | **PASS** |
| **Dependency Integrity** | `pip check` reports 0 conflicts | "No broken requirements found." | **PASS** |
| **Backend Health** | `GET /health` returns `200` | `{"status": "healthy"}` | **PASS** |
| **Database & PostGIS** | `GET /health/db` returns `200` & PostGIS 3.6.2 | `{"database": "connected", "postgis_version": "3.6 USE_GEOS=1 USE_PROJ=1 USE_STATS=1"}` | **PASS** |
| **Frontend Build** | `tsc -b && vite build` succeeds | Built clean in 161ms (`dist/` created) | **PASS** |
| **Frontend Lint** | `oxlint` reports 0 warnings/errors | 0 warnings, 0 errors across files | **PASS** |
| **Git Status & Secrets** | Clean/intended; `.env` untracked | `.env` untracked; 0 secrets exposed | **PASS** |
| **MCP Tooling** | PostgreSQL MCP connects read-only | `public` schema queried successfully (contains PostGIS tables) | **PASS** |

---

## 3. Existing Repository State vs. Target Requirements

### 3.1 Current Repository Layout
```text
Surakshit Basti/
├── backend/
│   ├── .venv/                      # Python 3.11.9 virtual environment (VERIFIED)
│   ├── app/
│   │   ├── api/                    # Empty directory
│   │   ├── engines/                # Empty directory
│   │   ├── models/                 # Empty directory
│   │   ├── schemas/                # Empty directory
│   │   ├── __init__.py             # Empty init
│   │   ├── database.py             # Working SQLAlchemy engine & PostGIS connection check
│   │   └── main.py                 # Working FastAPI app (/health, /health/db)
│   ├── tests/                      # Empty directory
│   └── requirements.txt            # Pinned dependencies (SQLAlchemy 2.1, GeoPandas 1.2, OR-Tools, etc.)
├── frontend/
│   ├── src/                        # Starter React shell (App.tsx, main.tsx, index.css)
│   ├── package.json                # Pinned dependencies (React 19, MapLibre GL 6, Turf, Recharts, Axios)
│   ├── package-lock.json
│   ├── tsconfig.json / .oxlintrc.json / vite.config.ts
│   └── dist/
├── data/
│   ├── cache/                      # Empty directory
│   ├── external/                   # Empty directory
│   ├── metadata/                   # Contains data_sources.csv (status of 4 verified data feeds)
│   ├── processed/                  # Empty directory
│   └── raw/                        # Empty directory
├── docs/                           # Empty directory
├── notebooks/                      # Empty directory
├── scripts/                        # Empty directory
├── .env                            # Untracked credentials & config (NAMES CHECKED ONLY)
├── .gitignore                      # Git ignore file
├── agent.md                        # Agent instructions & constraints (Source of truth §4)
├── app_flow.md                     # Application flows & sequence diagrams (Source of truth §3)
└── prd.md                          # Primary product requirements document (Source of truth §2)
```

---

## 4. Environment Variables in Use (Names Only)

The `.env` file was inspected for key presence without exposing values:
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (PostgreSQL / PostGIS connectivity)
- `EARTHDATA_TOKEN`, `PPS_USERNAME`, `PPS_PASSWORD`, `NASA_GPM_BASE_URL` (NASA GPM IMERG NRT access)
- `OSM_OVERPASS_URL` (OpenStreetMap query endpoint)
- `COPERNICUS_DEM_BUCKET`, `ESA_WORLDCOVER_BUCKET` (AWS public S3 bucket references)

---

## 5. Comprehensive Gap Analysis

| Module | What Exists | What PRD / APP_FLOW Requires | Gap / Planned Action |
|---|---|---|---|
| **Core & Settings** | Direct `os.getenv` in `database.py` | `pydantic-settings` based `core/settings.py`, structured JSON logging, provenance helper/enum | Create `app/core/settings.py`, `app/core/logging.py`, `app/core/provenance.py` in Phase 1 |
| **Migrations & DB Schema** | Tables in DB: only PostGIS system tables (`spatial_ref_sys`, etc.). No migration tool installed. | Alembic migrations with upgrade/downgrade for 11 entities: `districts`, `datasets`, `ingestion_runs`, `cells`, `habitations`, `sites`, `events`, `scenarios`, `assignments`, `rainfall_observations`, `capacity_norms`, `audit_log` | Add `alembic` (Phase 1); create initial schema migrations (Phase 2) |
| **Test Harness** | `backend/tests/` is empty; no test runner installed. | Unit, property, stress, API, and mocked ingestion tests | Add `pytest` + `httpx` (Phase 1) |
| **District Config** | None | Configurable `config/districts/<id>.yaml` (no hard-coded districts or bboxes) | Add district config schema & loader (Phase 1); pilot district YAML (Phase 3) |
| **Ingestion Clients** | Access credentials verified; `data_sources.csv` notes status | Idempotent CLI ingestion scripts for DEM, WorldCover, IMERG, and hybrid OSM ladder (Live → Cache → .pbf extract → Unavailable) | Implement `app/ingestion/` clients and manifests in Phase 3 |
| **Hazard Engine** | `app/engines/` is empty | Pure, deterministic raster & factor processing (slope, aspect, curvature, flow accumulation, wetness, HAND), weighted overlay baseline, dynamic rainfall multiplier, combined $H = 1 - \prod(1 - H_k)$ | Implement `hazard_engine.py` and terrain processing in Phase 4 |
| **Habitation & Urgency** | Empty | Habitation data loader/generator, vulnerability index (6 proxies with weights), urgency formula $U = H \times (0.5 + V) \times T \times \log(1 + P)$, 3-bucket classification | Implement `vulnerability_engine.py`, `urgency_engine.py` in Phase 5 |
| **Sites & Capacity** | Empty | GIS screening rules (slope, hazard, land use, roads, water), 3–8 candidate sites, multi-resource capacity $C_j = \min(C_{land}, C_{water}, C_{san}, C_{road}, C_{serv})$ with limiting factor | Implement `capacity_engine.py` and norms in Phase 6 |
| **Accessibility & Assignment** | Empty | NetworkX road-graph routing ($d_{ij}$ matrix), straight-line fallback, greedy assignment engine with decision paths, OR-Tools ILP solver, invariant tests | Implement `routing_engine.py`, `assignment_engine.py` in Phase 7 |
| **API Layer** | Root `/`, `/health`, `/health/db` | Versioned `/api/v1` routers: status, districts, hazard, habitations, sites, scenarios, assignments, validation, export, audit | Implement FastAPI v1 routers & services in Phase 8 |
| **Frontend UI** | Vite + React starter shell | Interactive MapLibre dashboard, hazard layers, threshold slider, rainfall-spike simulator, priority table, habitation detail & explanation panel, site fill bars, data status page, export | Build components, pages, map hooks, and API client in Phase 9 |
| **ML & Validation** | Empty | Random Forest / XGBoost + SHAP enhancement, spatially-blocked validation, model card, historical event backtest | Implement in Phase 10 |
| **Docs & Hardening** | Draft specs (`agent.md`, `app_flow.md`, `prd.md`) | ADRs in `docs/decisions/`, `docs/data_dictionary.md`, `docs/assumptions.md`, `docs/validation.md`, `.env.example` | Create documentation & `.env.example` progressively |

---

## 6. Pilot District Status & Recommendation

- **Current Status:** Pilot district is currently **pending user confirmation**.
- **Plumbing Note:** Previous DEM/WorldCover access checks used a Bengaluru tile strictly as a connectivity and plumbing test. Bengaluru does not satisfy the multi-hazard criteria.
- **PRD §7 Criteria:** Multi-hazard terrain (landslide + flood + cloudburst/flash flood), documented past event for backtest validation, and open data availability.
- **Recommendations for User Consideration:**
  1. **Wayanad District, Kerala** (High landslide + flood history, e.g. 2024 Meppadi/Chooralmala event, rich open data).
  2. **Idukki District, Kerala** (High landslide + flood terrain + dam/drainage networks).
  3. **Chamoli or Rudraprayag, Uttarakhand** (Landslide, cloudburst, flash flood history, e.g. 2021 Chamoli disaster).
  4. **Landslide/Flood District + Coastal Stretch** (e.g., Wayanad / Kozhikode or a combined coastal taluk scenario to demonstrate the static coastal erosion layer).

---

## 7. Next Steps (Phase 1 Transition)

Upon user approval, proceed to **Phase 1: Foundations**:
1. Implement `backend/app/core/settings.py` using `pydantic-settings`.
2. Implement `backend/app/core/logging.py` (structured context logging without secret leaks).
3. Implement `backend/app/core/provenance.py` (provenance envelope, freshness status, `DataOrigin` enum).
4. Implement GIS CRS verification helper `assert_same_crs`.
5. Implement District configuration loader (`config/districts/<id>.yaml`).
6. Submit Infrastructure Change Request for minimal required additions: `alembic` (schema migrations) and `pytest` + `httpx` (test harness).
7. Create baseline migration and skeleton `/api/v1/status` endpoint while keeping `/health` and `/health/db` intact.
