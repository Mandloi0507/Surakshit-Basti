# AGENTS.md — Surakshit Basti

> Instructions for AI coding agents (Antigravity, Claude Code, or similar) working in this repository.
> Read this file **fully** before touching anything. Then read `PRD.md` and `APP_FLOW.md`. These three files are the complete, self-contained specification; there is no other source document.

**Provenance tags used in all four planning documents**

| Tag | Meaning |
|---|---|
| `[PROJECT REQUIREMENT]` | A requirement of problem statement SIH26191 or the agreed MVP, as stated in `PRD.md` / `APP_FLOW.md` |
| `[CURRENT ENVIRONMENT FACT]` | A verified fact about the existing, working environment |
| `[ENGINEERING DECISION]` | A choice made here to fill a gap; not a problem-statement requirement |
| `[OPTIONAL FUTURE ENHANCEMENT]` | Not needed for MVP; implement only if explicitly requested |

---

## 0. DO NOT BREAK THE VERIFIED ENVIRONMENT

`[CURRENT ENVIRONMENT FACT]` The environment below has been created **and verified**. It is stable infrastructure. Your job is to build **on top of it**.

### What "do not break" means, precisely

**Never, without an explicit written justification approved by the user:**

1. Reinstall, upgrade, downgrade, or replace any package pinned in `backend/requirements.txt` or `frontend/package.json`. (Pinned versions are what was verified. Do not run `pip install -U`, `pip install --upgrade`, `npm update`, `npm audit fix --force`, or regenerate lockfiles.)
2. Create a second virtual environment. The one and only venv is `backend/.venv` (Python 3.11.9).
3. Create a second database, a second PostGIS install, or a second Postgres container. The one database is `surakshit_basti` (PostgreSQL 17, PostGIS 3.6.2).
4. Replace FastAPI, SQLAlchemy, GeoAlchemy2, React, Vite, MapLibre GL JS, Turf.js, Recharts, Axios, React Router, or Lucide React.
5. Modify, rename, or delete working endpoints: `GET /health` and `GET /health/db` must keep returning what they return today (DB connectivity + PostGIS version).
6. Change the NASA PPS / Earthdata authentication setup, its `.env` keys, or its token flow. It was tested successfully (HTTP 200). **Treat it as read-only.** You may *call* it through a thin client; you may not re-implement or re-key it.
7. Touch the read-only `mcp_readonly` DB user, or turn `PG_ALLOW_WRITE` to `true`.
8. Overwrite `.env`, commit `.env`, or print any value from it.
9. Rewrite Git history, force-push `main`, or delete the "initial environment commit".
10. Restructure the repository layout (move `backend/app/*`, rename top-level folders) without a documented reason.
11. Remove or overwrite working code or files. Extend them, or add new modules next to them.

**Always, before and after every change:**

- Run the **baseline verification checklist**  and confirm it is still green.
- If anything in the checklist turns red, **stop, revert your change, and report**. Do not "fix forward" by modifying infrastructure.

### 0.1 Baseline verification checklist (run at start and after each phase)

```text
[ ] backend/.venv activates; `python --version` → 3.11.9
[ ] `pip check` reports no new conflicts (do NOT run pip install to "fix" anything)
[ ] uvicorn app.main:app starts from backend/
[ ] GET /health   → 200
[ ] GET /health/db → 200, reports database connectivity and PostGIS version (3.6.2)
[ ] `cd frontend && npm run build` succeeds (tsc -b && vite build)
[ ] `npm run lint` (oxlint) shows no new errors
[ ] `git status` shows only intended changes; .env is not tracked
[ ] backend tests pass (once a test suite exists)
```

### 0.2 If you believe a change to infrastructure is required

Stop. Write a short **Infrastructure Change Request** (what, why, alternatives considered, compatibility check against pinned versions, rollback plan) in `docs/decisions/` and ask the user. Do not proceed unprompted.

---

## 1. Project overview

**Surakshit Basti — Proactive Relocation Intelligence for Disaster-Prone Habitations** (SIH26191, Ministry of Home Affairs / NDRF DM Division, Software, Disaster Management). The name "Surakshit Basti" is the working project name used in the current environment.

A GIS decision-support platform that, in one pipeline:
1. identifies and continuously updates multi-hazard **Red Zones** (landslide, flood, cloudburst/flash flood, coastal erosion);
2. assesses **carrying capacity** of candidate relocation sites;
3. ranks habitations for **Immediate / Short-term / Medium-term** relocation using hazard × vulnerability × time, and **assigns** them to sites within capacity, with a reason for every decision.

`[PROJECT REQUIREMENT]` The differentiator is Part 3: the capacity-constrained, vulnerability-weighted, explainable assignment engine. Hazard maps alone are not the product.

MVP scope: **ONE real pilot district**, configurable. No national scale.

## 2. Source-of-truth hierarchy

When documents disagree, the higher one wins:

1. **The user's latest explicit instruction** in the current session.
2. **`PRD.md`** (primary source: problem, MVP scope, formulas, thresholds, data sources, out-of-scope, acceptance criteria).
3. **`APP_FLOW.md`** (flows and sequencing; must agree with the PRD — if they differ, the PRD wins and you must flag the discrepancy).
4. **This `AGENTS.md`** (rules of engagement; applies to *how* you work, and never relaxes a PRD requirement).
5. **Actual repository state** (inspect it; never assume folders contain logic).
6. Your own preferences. (Lowest.)

If something is ambiguous: identify the ambiguity, choose the **safest** assumption, record it in `docs/decisions/` as an `[ENGINEERING DECISION]`, and tell the user.

## 3. Repository structure

`[CURRENT ENVIRONMENT FACT]` (approximate; **inspect before assuming**)

```text
Surakshit Basti/
├── backend/
│   ├── app/
│   │   ├── api/         # routers
│   │   ├── engines/     # domain logic (hazard, vulnerability, urgency, capacity, routing, assignment)
│   │   ├── models/      # SQLAlchemy / GeoAlchemy2 models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── database.py
│   ├── tests/
│   ├── .venv/
│   └── requirements.txt
├── frontend/            # React + TS + Vite
├── data/                # raw/ processed/ cache/ metadata/ external/
├── docs/
├── notebooks/
├── scripts/
├── .env
└── .gitignore
```

`[ENGINEERING DECISION]` Additions are allowed **inside** this structure (new sub-packages), e.g.:

```text
backend/app/core/            # settings, logging, provenance helpers (new)
backend/app/ingestion/       # source clients: imerg, copernicus_dem, worldcover, osm (new)
backend/app/services/        # orchestration between api, engines, db (new)
backend/migrations/          # schema migrations (see §9)
data/metadata/               # dataset manifests (JSON/YAML)
docs/decisions/              # ADRs
```

## 4. Environment constraints

`[CURRENT ENVIRONMENT FACT]`

- OS Windows; IDE Antigravity / VS Code-compatible; WSL2 + Ubuntu + Docker + Docker Compose available.
- Python **3.11.9**, venv **`backend/.venv`**. Windows shell: use `backend\.venv\Scripts\activate`. Use forward-slash-safe paths in code (`pathlib.Path`). Never hard-code `C:\...`.
- Backend: FastAPI 0.142.2, Uvicorn, Pydantic 2 + pydantic-settings, SQLAlchemy 2.1.x, GeoAlchemy2, psycopg2-binary.
- GIS: GeoPandas, Shapely 2, Rasterio, PyProj, Xarray, NumPy 2.x, Pandas 3.x, SciPy, pyogrio.
- ML/Opt: scikit-learn, XGBoost, SHAP, OR-Tools, NetworkX.
- Also already pinned: `boto3` (used for public S3 access — see data rules), `requests`, `numba`, `PyYAML`, `python-dotenv`, `tqdm`.
- DB: PostgreSQL 17 + PostGIS 3.6.2, database `surakshit_basti`.
- Frontend: React 19, TypeScript ~6.0, Vite 8, maplibre-gl 6, @turf/turf 7, recharts 3, axios, react-router-dom 7, lucide-react, oxlint.

**Notable gaps (do not "fix" silently):**
- No migration tool is pinned (Alembic absent), no test runner pinned (pytest absent), and no task queue (Celery/Redis are **not** installed). See §10 for how to handle.
- Pandas 3 / NumPy 2 are new major versions: write code that is compatible with them; do not downgrade to match old tutorials.

## 4.1 Important data-vs-pilot note

`[CURRENT ENVIRONMENT FACT]` Copernicus DEM and ESA WorldCover access was verified against a **Bengaluru-area tile**. `[PROJECT REQUIREMENT]` The pilot-district criteria (PRD §7) require multi-hazard terrain with a documented past event (candidates: Wayanad, Chamoli/Rudraprayag, Idukki, Kalimpong/Darjeeling, a coastal taluk). Bengaluru-area tiles are therefore a **connectivity/plumbing test**, not a pilot. **The pilot district is still pending.** Do not hard-code Bengaluru as the pilot; do not download a regional OSM extract until the pilot is selected.

---

## 5. Backend rules

- Layering: `api` (routers, validation, HTTP only) → `services` (orchestration, transactions) → `engines` (pure domain logic) → `models`/DB.
- **Engines are pure and deterministic**: no HTTP, no DB session, no global state, no clocks (inject `now`), no randomness without a seed. Inputs and outputs are typed dataclasses/Pydantic models or GeoDataFrames/arrays. `[PROJECT REQUIREMENT]` (core logic separate from interface; unit-tested plain Python package).
- Config only through `pydantic-settings`. No `os.environ[...]` scattered in code.
- Use dependency-injected DB sessions; do not open ad-hoc connections.
- Long computations (raster processing, ML training, ILP) run as **scripts/CLI jobs or FastAPI background tasks**; do not introduce Celery/Redis for MVP. `[ENGINEERING DECISION]`
- Never block the event loop with heavy CPU in `async def`; use sync endpoints (`def`) or a threadpool for CPU work.
- Type-hint everything; keep functions small; docstrings on every public function stating units and CRS where relevant.

## 6. Frontend rules

- Keep React + TypeScript + Vite. `strict` TS. No `any` without a comment.
- Map: **MapLibre GL JS** only. Turf.js for light client-side geometry; heavy GIS stays in backend. No Leaflet, no Mapbox token-requiring styles. Use a free basemap style/raster tiles that need no key (or a local blank style). `[ENGINEERING DECISION]`
- Charts: Recharts. Icons: Lucide. HTTP: Axios via a single API client module. Routing: React Router.
- The frontend **never** talks to NASA, AWS, Overpass, or the database. It talks to FastAPI only.
- The frontend **never** contains secrets and never reads `.env`. Only `VITE_`-prefixed non-secret values (e.g. API base URL).
- Every number shown must come from the API. The UI never recomputes hazard, urgency, capacity, or assignment (exception: display-only formatting/sorting).
- Every data panel shows a **data-status badge**: `LIVE`, `CACHED`, `DEMO/SYNTHETIC` (plus `STALE`/`UNAVAILABLE` where applicable) and an "as of" timestamp. `[PROJECT REQUIREMENT]` (label synthetic data; show provenance & uncertainty).
- Use large fonts and high-contrast map styling (demo projected on a projector). `[PROJECT REQUIREMENT]`
- Accessibility basics and mobile responsiveness are targets, not blockers. `[PROJECT REQUIREMENT]` (hardening phase)

## 7. GIS rules

- **CRS discipline.** Store geometry in PostGIS as **EPSG:4326** (`geometry(…,4326)`). Do metric computations (area, buffers, distance, slope on a grid) in a **projected metric CRS appropriate to the pilot** (UTM zone derived from the district centroid, e.g. EPSG:32643 / 32644 for most of India) — never compute metres/areas in 4326. `[ENGINEERING DECISION]`
- Before **every** spatial join/overlay: assert both inputs have a CRS and that they match; reproject explicitly; raise if CRS is `None`. Provide and use a helper `assert_same_crs(a, b)`.
- Rasters: use Rasterio; keep nodata handling explicit; align rasters to a single reference grid (resolution, transform, CRS) before combining. Document resolution (30 m source rasters, aggregated to 100–250 m cells). `[PROJECT REQUIREMENT]`
- Clip everything to the pilot district boundary (configurable).
- Never mutate raw files. Processed outputs go to `data/processed/<dataset>/<version>/`.
- Record units in column names or docs (`slope_deg`, `dist_road_m`).
- Use `pathlib`, `pyogrio`-backed GeoPandas I/O. Prefer GeoPackage / Parquet / Cloud-Optimised GeoTIFF for processed outputs.

## 8. Database & PostGIS rules

- One DB: `surakshit_basti`. Credentials come from `.env` (`DATABASE_URL` or the existing equivalent keys — **read the existing `database.py`/settings to learn the actual names; do not rename them**).
- All spatial columns: GeoAlchemy2 `Geometry(geometry_type, srid=4326)` with a **GiST index**. Raster-derived grids are stored as vector cells (`Cell`) or as files referenced by metadata; do not enable `postgis_raster` unless justified. `[ENGINEERING DECISION]`
- Schema changes **only via migrations** (see §9), never via `Base.metadata.create_all()` in app startup and never by hand-editing the DB.
- The app's DB user needs write access; the **`mcp_readonly`** user must stay read-only. When adding tables, make sure `mcp_readonly` still has `SELECT` where intended, but never grant it write privileges.
- Use transactions; use `ST_Transform`, `ST_DWithin` on geography or projected geometry appropriately; avoid `ST_Distance` on 4326 geometry for metres.
- Name tables `snake_case` singular or plural consistently (choose plural: `habitations`, `sites`, `cells`, `events`, `scenarios`, `audit_log`), PK `id`, timestamps `created_at`/`updated_at` in UTC (`timestamptz`).
- Seed/demo data: separate seed scripts in `scripts/`, every row carrying `data_origin` (see §12).

## 9. Migrations

`[ENGINEERING DECISION]` Schema changes must use migrations. Alembic is the standard choice for SQLAlchemy but is **not currently installed**. Adding it is a justified, minimal dependency addition: it is pure Python, SQLAlchemy-2-compatible, and does not alter the existing stack. Before adding: check that the chosen Alembic version supports the pinned SQLAlchemy 2.1.x; install **only** that package into `backend/.venv`; append the pinned version to `requirements.txt`; commit separately. Configure `env.py` to read the existing settings/URL and to ignore PostGIS system tables (`spatial_ref_sys`, topology/tiger tables) in autogenerate. Review every autogenerated migration by hand. Every migration needs a working `downgrade()` or an explicit comment why not.

## 10. Dependency rules

1. Default answer to "can I add a dependency?" is **no**. Use what is pinned.
2. If genuinely needed: justify in `docs/decisions/`, verify compatibility with Python 3.11.9, NumPy 2.4, Pandas 3, SQLAlchemy 2.1, Pydantic 2.13; install the **single** package; pin it; run the baseline checklist; commit alone.
3. Likely justified additions (still ask/record): `alembic` (migrations), `pytest` + `httpx` (tests; `TestClient` needs `httpx`), `pyosmium` or `osmium` tooling **or** `pyrosm`/`ogr2ogr` for `.osm.pbf` reading (check Windows wheels first; GDAL via Rasterio/pyogrio's OSM driver may already read `.pbf` — try that first). `[ENGINEERING DECISION]`
4. Never add: ORMs besides SQLAlchemy, a second web framework, a task queue (MVP), a second map library, a CSS framework without need, Earth Engine SDK (cloud-native option — out of MVP).
5. Never run bulk upgrade commands. Never delete `package-lock.json` or `requirements.txt` pins.

## 11. Data ingestion rules

Philosophy `[CURRENT ENVIRONMENT FACT]`: **REAL DATA FIRST → CACHED/LOCAL SECOND → INTELLIGENT FALLBACK THIRD → NEVER FAKE LIVE DATA.**

1. Preserve raw downloads untouched in `data/raw/<source>/<dataset>/<version-or-date>/`. Never edit; checksum them (SHA-256) in the manifest.
2. Processed outputs separate: `data/processed/`. Scratch/cache: `data/cache/`.
3. Every dataset has a metadata manifest in `data/metadata/` with: `source`, `dataset`, `version`, `license`, `access_date`, `bbox/district`, `crs`, `resolution`, `checksum`, `processing_status`, `script` (path + git commit), `data_origin` (`LIVE|CACHED|DEMO_SYNTHETIC`).
4. Ingestion is **separate from the request path**: external sources → ingestion/validation → raw/cache → processing → PostGIS → application. API handlers must not call external services synchronously on the user's click path, except via an explicit "refresh" action that degrades gracefully.
5. Every ingestion script is **idempotent and re-runnable** and exposes a CLI (`python -m app.ingestion.<name> --district <id> ...`).
6. Validate on ingest: CRS present, bbox covers district, nodata share sane, value ranges plausible (slope 0–90°, rainfall ≥ 0), non-empty geometries.
7. Always respect licences and note them (Copernicus DEM, ESA WorldCover CC-BY 4.0, OSM ODbL, NASA GPM open data). Record attribution text for the UI footer. `[PROJECT REQUIREMENT]` (record licence and access date).

### Source specifics

- **NASA GPM IMERG** `[CURRENT ENVIRONMENT FACT]`: Earthdata account, PPS registration, Near-Real-time access configured; PPS auth tested (HTTP 200); credentials are in `.env`. **Use the existing credential keys. Do not replace the auth setup, do not ask the user to re-register, do not add a new auth library that changes the flow.** Wrap access in `app/ingestion/imerg.py` using `requests` with credentials read from settings; redact secrets in logs; support a `--dry-run` that only checks reachability.
- **Copernicus DEM (GLO-30)** `[CURRENT ENVIRONMENT FACT]`: public AWS S3, no key; use unsigned/anonymous access (`boto3` with `signature_version=UNSIGNED`) or HTTPS. Select tiles by district bbox, never hard-code the Bengaluru tile.
- **ESA WorldCover 2021 v200** `[CURRENT ENVIRONMENT FACT]`: public S3, no key; same pattern.
- **OpenStreetMap** `[CURRENT ENVIRONMENT FACT]`: hybrid. Public Overpass proved unreliable/rate-limited. Strategy:

```text
LIVE OSM (Overpass, short timeout, polite, single attempt + capped retry, optional)
   │ success → validate → write to data/cache/osm/ (timestamped) → process → PostGIS   [status: LIVE]
   │ failure/timeout/429
   ▼
CACHED OSM (data/cache/osm/, newest valid file)                                        [status: CACHED, age shown]
   │ no cache
   ▼
REGIONAL OSM EXTRACT (.osm.pbf in data/external/osm/ or data/raw/osm/)                 [status: CACHED/EXTRACT, extract date shown]
   │ none present
   ▼
UNAVAILABLE → routing/access features report "unavailable" (no fake roads)
```

  The regional extract is **not yet downloaded**; do not download it until the pilot district is chosen. The application must **never** depend directly on Overpass being up.

## 12. Live / cached / demo labelling

`[PROJECT REQUIREMENT]` (label synthetic data, show provenance) + `[CURRENT ENVIRONMENT FACT]` (explicitly distinguish LIVE, CACHED, DEMO/SYNTHETIC).

Every dataset, table row batch, API response, and UI panel carries a **provenance envelope**:

```json
{
  "data_origin": "LIVE | CACHED | DEMO_SYNTHETIC",
  "source": "NASA GPM IMERG Early/Late Run",
  "retrieved_at": "2026-10-07T06:00:00Z",
  "valid_time": "2026-10-07T05:30:00Z",
  "age_seconds": 1800,
  "freshness": "FRESH | STALE | UNKNOWN",
  "license": "…",
  "notes": "…"
}
```

Rules:
- `LIVE` = fetched from the external source during the current refresh cycle, validated.
- `CACHED` = previously fetched real data served from local storage; always show its age.
- `DEMO_SYNTHETIC` = generated by us (demographics, candidate-site attributes where official data are not public). `[PROJECT REQUIREMENT]` allows synthetic-but-realistic demographics and sites, **clearly labelled**.
- **Never** relabel CACHED as LIVE. **Never** substitute synthetic for real silently. If real data is missing, return `UNAVAILABLE` with a reason, or an explicitly-labelled fallback.
- Synthetic generators must be seeded, versioned, documented, and stored with `data_origin='DEMO_SYNTHETIC'` in each row.
- Derived outputs inherit the **weakest** origin of their inputs (e.g. a hazard score using synthetic inputs is not "real").

## 13. External data failures

- Timeouts on every network call (connect ≤ 10 s, read ≤ 30 s unless downloading large files, then streaming with resume).
- Bounded retries with exponential backoff + jitter; never hammer Overpass or PPS.
- Circuit-breaker-style behaviour: after N consecutive failures, skip live attempts for a cool-down window and serve cache.
- On failure: log (without secrets), fall down the ladder (§11), set status/freshness, surface a user-visible banner. Never crash the app, never return a 500 for "external source down".
- Rainfall specifically: if IMERG is unavailable, use the latest cached rainfall; if none, the dynamic layer is shown as `UNAVAILABLE` and the **structural** Red Zones remain (they do not depend on live rainfall). The manual rainfall-spike **simulator** continues to work (it is a what-if, labelled `SIMULATED`, never `LIVE`). `[ENGINEERING DECISION]`

## 14. API rules

- Versioned prefix `/api/v1/…`; keep `/health` and `/health/db` exactly as is (unversioned).
- Pydantic response models for every endpoint; no raw dicts of DB rows.
- Geospatial responses as **GeoJSON** (RFC 7946, EPSG:4326). Large layers: bounding-box filtering and/or simplified geometry; vector tiles are `[OPTIONAL FUTURE ENHANCEMENT]`.
- Every response that contains computed or ingested data includes the provenance envelope (§12).
- Consistent error shape: `{ "error": { "code": "…", "message": "…", "details": … } }`. 4xx for caller errors, 503 + `UNAVAILABLE` info for missing required data, never leak stack traces or secrets.
- Idempotent GETs; POST for scenario/what-if runs; scenario runs never mutate baseline data.
- CORS: restrict to the dev frontend origin from settings.
- No endpoint ever returns credentials, DB URLs, or raw environment values.

## 15. ML rules

`[PROJECT REQUIREMENT]` Start with a **transparent weighted overlay** (AHP/equal weights) baseline; ML (Random Forest / XGBoost + SHAP) is an **enhancement** with validation numbers, not a replacement for the baseline.
- Split train/validation **spatially** (blocked/grouped) to avoid leakage; report AUC, precision, recall, confusion matrix at the chosen threshold.
- Fix random seeds; persist model + feature list + training-data manifest + metrics ("model card") under `data/processed/models/<name>/<version>/`.
- Explainability via SHAP: per-cell/per-habitation top factor contributions.
- Backtest on at least one documented past event using only data available before it. `[PROJECT REQUIREMENT]`
- If no landslide inventory is available for the pilot, say so; fall back to weighted overlay and label accordingly. Never fabricate inventory points.
- ML outputs are scores in [0,1]; the rest of the system must be able to run on the weighted-overlay score alone.
- LLM rule: deterministic engines produce all numbers. An LLM (if ever used) may only **explain/summarise** already-computed results. It must not invent or alter hazard, population, capacity, risk, or assignment values. LLM use is `[OPTIONAL FUTURE ENHANCEMENT]`; no LLM API key may be introduced without user approval.

## 16. Optimisation rules

- Implement **greedy baseline first**, then **ILP/CP-SAT via OR-Tools** (already pinned) with the PRD objective (§17); compare both. `[PROJECT REQUIREMENT]`
- Tie-breaking order: higher vulnerability → larger population → shorter distance. Deterministic final tiebreak by `id` ascending. `[ENGINEERING DECISION]` (final tiebreak)
- **Hard invariants (property-tested):** no site exceeds capacity; every habitation is either assigned or has an explicit `unassigned_reason`; ineligible pairs never assigned; results are reproducible for identical inputs.
- Use integer arithmetic for capacities/populations in solvers (scale if needed).
- NetworkX for road-graph routing / distance matrices; precompute and cache the habitation×site matrix.
- Solver time limit and a greedy fallback if the solver fails or times out.

## 17. Testing rules

- Add `pytest` (see §10). Tests in `backend/tests/` mirroring `app/` structure.
- Required: unit tests per engine (score ranges 0–1, formula correctness against hand-computed examples, bucket thresholds), property tests for assignment invariants, randomised stress tests with shrinking capacity, sensitivity test (±20% weights → report changed ranks), API tests with `TestClient`, ingestion tests with **mocked** network (never hit PPS/S3/Overpass in unit tests), CRS-mismatch tests.
- Keep integration tests that touch the DB separate (marker `db`) and run against `surakshit_basti` only with non-destructive, transaction-rolled-back tests — or a clearly-named throwaway schema. Never drop/truncate real data in tests.
- Frontend: `npm run build` and `npm run lint` must pass; add component tests only if a runner is approved.
- Run the baseline checklist  + the new tests after every phase.

## 18. Security & environment variables

- Secrets only in `.env` (git-ignored). Never commit `.env`; verify `.gitignore` covers `.env`, `.env.*` (except `.env.example`), `data/raw`, `data/cache`, `data/processed` large files, `.venv`, `node_modules`.
- Provide/maintain `.env.example` with **names only and placeholder values**. Never copy real values.
- **Never print, log, echo, or paste** secrets (API tokens, PPS credentials, DB passwords). Mask in logs (`****`). Do not `cat .env` into your output; if you must verify keys exist, check **presence only** (`bool(settings.X)`).
- Never put credentials in frontend code, Vite env (`VITE_*`), API responses, error messages, notebooks, or commit messages.
- Parameterised queries only (SQLAlchemy); no string-built SQL with user input.
- Validate/limit user inputs (rainfall multiplier range, weight ranges, bbox size).
- `[PROJECT REQUIREMENT]` Human-in-the-loop: outputs are recommendations; officer override and an audit log are required (Should-level in MVP).

## 19. MCP rules

`[CURRENT ENVIRONMENT FACT]` PostgreSQL MCP is configured, read-only (`mcp_readonly`, `PG_ALLOW_WRITE=false`), tested for current database, user, PostGIS version.
- MCP is a **developer/agent inspection tool**, not part of the deployed architecture. The application must not import or depend on MCP.
- Use it to inspect schema and verify data, e.g. check a migration applied. Never attempt writes through it. Never reconfigure it.
- Schema changes go through migrations run by the app's DB user, not through MCP.

## 20. Git rules

- Branch from `main`; one branch per phase/feature: `phase-3/ingestion-dem`, `fix/…`. Small, reviewable commits.
- Conventional-style messages: `feat(hazard): …`, `fix(api): …`, `chore(deps): …`, `docs: …`, `test: …`.
- Commit lockfile/requirements changes **separately** from feature code.
- Before committing: baseline checklist, `git diff --stat`, confirm no secrets and no large data files staged.
- Never force-push `main`, never rewrite pushed history, never commit data/raw dumps (track manifests, not bulk data; consider Git LFS only if approved).
- Tag phase completion: `phase-N-complete`.

## 21. Naming & code organisation

- Python: `snake_case` modules/functions, `PascalCase` classes, `UPPER_SNAKE` constants. Engines: `backend/app/engines/<name>_engine.py` (`hazard_engine.py`, `vulnerability_engine.py`, `urgency_engine.py`, `capacity_engine.py`, `routing_engine.py`, `assignment_engine.py`).
- Schemas: `app/schemas/<entity>.py` (`HabitationOut`, `SiteOut`, `ScenarioIn`).
- Models: `app/models/<entity>.py`.
- Routers: `app/api/v1/<resource>.py`.
- TS: `PascalCase.tsx` components, `camelCase` functions, `src/api/`, `src/components/`, `src/pages/`, `src/hooks/`, `src/types/`, `src/map/`.
- Units/CRS in names. Config constants live in settings or `config/` YAML, **not** inline magic numbers.
- Formula weights/thresholds come from config with the defaults specified in the PRD; never hard-code in logic.

## 22. Error handling & logging

- Fail loudly in engines (raise typed exceptions: `CRSMismatchError`, `DataUnavailableError`, `InvalidConfigError`); catch at the service/API boundary and translate.
- Use Python `logging` (structured/JSON-friendly format), one logger per module, levels used properly. Include `request_id`, `district_id`, `scenario_id`, `dataset`, `data_origin`. Never log secrets, full `.env`, or full DB URLs.
- Log every external call outcome (success/failure/duration/status code, no credentials) and every fallback transition.
- Ingestion jobs write a run record (start/end, rows, status, origin) to the DB or manifest.

## 23. Documentation requirements

- Keep `README.md` current (setup, run, verify).
- Every phase adds/updates docs; every major architectural choice gets an ADR in `docs/decisions/NNNN-title.md` (context, decision, alternatives, consequences, tag `[ENGINEERING DECISION]`).
- Maintain `docs/data_dictionary.md`, `docs/assumptions.md` (all synthetic/proxy data and capacity norms), `docs/validation.md`, `docs/api.md`.

## 24. Rules for modifying existing files

1. Read the file and its callers first.
2. Prefer **additive** changes (new module/route/component) over edits.
3. Make the smallest diff that works; no drive-by reformatting, renaming, or reorganising.
4. Never overwrite a file with a whole new version unless it is empty/placeholder and you have verified that.
5. `main.py`: only add `include_router(...)` lines and startup wiring; leave `/health` and `/health/db` intact.
6. `database.py`: do not change engine/session creation semantics; extend only if required and tested.
7. `requirements.txt` / `package.json` / lockfiles: see §10.
8. After the edit, run the baseline checklist.

## 25. Reproducibility

- A single documented command (or short script sequence in `scripts/`) rebuilds all processed layers for a district from raw data. `[PROJECT REQUIREMENT]` (data-foundation exit criterion).
- All scripts take `--district` / config file; pilot district is configuration (`config/districts/<id>.yaml`), never code. `[PROJECT REQUIREMENT]` (“another district is a configuration change, not a rewrite”).
- Seeds fixed; versions recorded; manifests list input checksums and git commit.
- No notebook-only logic: notebooks explore; production logic lives in `app/` and `scripts/`.

## 26. Working protocol (summary)

For each phase: **inspect → explain plan → smallest change → test → verify baseline → report → next.** Never run the whole project in one go. Stop and ask when facing an ambiguity that could break verified infrastructure or invalidate PRD requirements.