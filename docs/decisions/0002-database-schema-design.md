# 0002. Core Domain Database Schema & Spatial Modeling

**Status:** Accepted  
**Date:** 2026-10-08  
**Tag:** `[ENGINEERING DECISION]`

---

## Context
Per PRD §23 and APP_FLOW §21, Surakshit Basti requires a relational and geospatial data architecture to store multi-hazard cells, habitations with vulnerability/urgency scores, candidate relocation sites with multi-resource capacities, historical events for backtesting, what-if scenarios, assignment decision paths, rainfall observations, capacity norms, and audit logs.

## Decision
1. Create 12 relational tables in PostgreSQL 17 / PostGIS 3.6.2:
   - `districts`: Pilot and multi-district administrative boundary and coordinate reference metadata.
   - `datasets`: Manifest metadata mirror for tracked data sources with checksums and status.
   - `ingestion_runs`: Execution logs for data pipelines with origin and duration.
   - `cells`: Vector grid representations of 100m–250m terrain cells holding raw factor attributes, individual hazard scores, combined hazard $H$, hazard class (Red/Amber/Green), and factor contributions.
   - `habitations`: Settlement locations (points/footprints) with demographic vulnerability proxies, inherited hazard score, composite urgency $U$, classification bucket, and assigned site references.
   - `sites`: Candidate relocation sites with geometric attributes, multi-resource capacities ($C_{land}, C_{water}, C_{sanitation}, C_{road}, C_{services}$), limiting factor, allocated population, and screening reasons.
   - `events`: Historical disaster events (landslides, flash floods) for validation and backtesting.
   - `scenarios`: What-if simulation parameters (rainfall multipliers, weight adjustments, site capacity overrides).
   - `assignments`: Capacity-constrained habitation-to-site assignments with deterministic decision explanations and routing metrics.
   - `rainfall_observations`: Live and historical IMERG / gridded rainfall records with provenance.
   - `capacity_norms`: Sourced housing/water/sanitation planning norms for temporary and permanent sites.
   - `audit_log`: Officer and system action logs with before/after state snapshots.
2. **Spatial Modeling**:
   - All spatial geometries stored in **EPSG:4326** (`geometry(Geometry, 4326)`).
   - GiST spatial indexes (`idx_<table>_geometry`) created on all geometry columns.
3. **Data Provenance**:
   - Ingested and derived tables carry `data_origin` (`LIVE`, `CACHED`, `DEMO_SYNTHETIC`, `SIMULATED`, `UNAVAILABLE`) and `retrieved_at` timestamp.
4. **Security & Permissions**:
   - Database operations executed by the application database user; `mcp_readonly` retains `SELECT` permissions.
