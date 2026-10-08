# 0003. Data Ingestion Architecture & Fallback Ladder

**Status:** Accepted  
**Date:** 2026-10-08  
**Tag:** `[ENGINEERING DECISION]`

---

## Context
Per PRD §19, §26 and AGENTS.md §11, Surakshit Basti requires an automated, idempotent data ingestion architecture covering four primary external feeds:
1. **Copernicus DEM (GLO-30)**: Public AWS S3 unsigned access for 30m digital elevation data.
2. **ESA WorldCover 2021 v200**: Public AWS S3 unsigned access for 10m land use / land cover rasters.
3. **NASA GPM IMERG NRT**: Near-real-time precipitation data via NASA PPS / Earthdata authentication.
4. **OpenStreetMap**: Hybrid road network, drainage, and critical facility extraction via a strict fallback ladder.

## Decision
1. **Ingestion Separation from Request Path**:
   - Ingestion jobs execute offline or via background CLI pipelines (`python -m backend.app.ingestion.<module> --district <id>`), never blocking user request cycles synchronously.
2. **Raw File Immutability & Checksums**:
   - Downloaded raw data is preserved untouched in `data/raw/<source>/<dataset>/` and SHA-256 checksummed in metadata manifests (`data/metadata/<district>_<dataset>_manifest.json`).
3. **OpenStreetMap Ingestion Ladder**:
   - Tier 1: `LIVE` Overpass API query (10s timeout, bounded retry).
   - Tier 2: `CACHED` local query result from `data/cache/osm/`.
   - Tier 3: `CACHED_EXTRACT` regional `.osm.pbf` extract.
   - Tier 4: `UNAVAILABLE` fallback with graceful degradation (no fake road networks).
4. **NASA PPS Credentials**:
   - Reuses configured `.env` credentials (`PPS_USERNAME`, `PPS_PASSWORD`, `EARTHDATA_TOKEN`) via `Settings`. Supports `--dry-run` Reachability mode.
5. **Tile Resolution Calculation**:
   - Bounding box tiles are dynamically derived from the active district configuration.
6. **Automated Testing**:
   - Unit tests use mocked network responses to test normal execution and error fallback transitions without hitting external remote endpoints.
