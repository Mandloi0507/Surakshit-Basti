# PRD.md — Surakshit Basti: Product Requirements Document

**Product:** Surakshit Basti — Proactive Relocation Intelligence for Disaster-Prone Habitations
**Problem statement:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations (MHA / NDRF DM Division; Software; Disaster Management)
**Status:** Draft v1 — planning only (no implementation yet)

Tags: `[PROJECT REQUIREMENT]` · `[CURRENT ENVIRONMENT FACT]` · `[ENGINEERING DECISION]` · `[OPTIONAL FUTURE ENHANCEMENT]`

Requirement IDs: `FR-` functional, `NFR-` non-functional. Priorities use Must / Should / Could.

**This PRD is the primary source of truth for the project.** `APP_FLOW.md` details the flows; `AGENTS.md` defines how coding agents must work. Together they are self-contained.

---

## 1. Product vision `[PROJECT REQUIREMENT]`

Move authorities from reactive rescue to proactive relocation: a GIS decision-support platform that shows officials where it is unsafe, where people can go, and who should move first, with a reason for every decision.

## 2. Problem statement `[PROJECT REQUIREMENT]`

Vulnerable habitations remain in landslide, flood, cloudburst and coastal-erosion zones; relocation usually begins after loss. Hazard maps, census, land availability and planning sit in different agencies; zonation is static; destination sites' capacity is ignored; vulnerability is under-used; prioritisation is manual, hard to audit, has no time horizons, no what-if, and limited explainability.

## 3. Target users `[PROJECT REQUIREMENT]`

SDMA officials (primary); District Collector/DDMA; NDRF/SDRF planners; Gram Panchayat/block officials; town-planning/revenue departments; vulnerable communities (indirect); NGOs/humanitarian agencies; researchers/insurers (secondary).

## 4. Personas `[ENGINEERING DECISION]` (derived from the problem statement's stakeholder analysis)

| Persona | Goal | Key need |
|---|---|---|
| **State planner (SDMA)** | Justify relocation spending | Ranked state/district list, budget-ready exports |
| **District Collector (DDMA)** | Decide fast in monsoon | Live red-zone map, Immediate list, site fill levels, clear reasons |
| **NDRF/SDRF planner** | Pre-position resources | Dynamic hotspots, access routes, likely volumes |
| **Block/Panchayat officer** | Convince residents | Simple habitation profile, printable summary |
| **Land/revenue planner** | Find buildable safe land | Ranked candidate sites with slope/land-use/infrastructure checks |

## 5. Goals `[PROJECT REQUIREMENT]`

G1 Dynamic multi-hazard Red Zones. G2 Site carrying-capacity assessment with limiting factor. G3 Vulnerability-weighted urgency (hazard × vulnerability × time). G4 Capacity-constrained assignment with three buckets and reasons. G5 Interactive GIS dashboard with what-if and exports. G6 Transparency: provenance, uncertainty, adjustable weights/thresholds, audit log.

## 6. Non-goals

N1 National scale. N2 Replacing consultation/consent (tool is decision support; human-in-the-loop). N3 Legal land-title/compensation workflows. N4 Detailed engineering design of sites. N5 Mobile field apps. N6 Live integration with government pipelines. (All `[PROJECT REQUIREMENT]` out-of-scope items, §3.3.)

## 7. MVP scope `[PROJECT REQUIREMENT]`

For **one real pilot district** (selection **pending**, configurable): (a) multi-hazard Red Zone map that updates when rainfall changes; (b) candidate relocation sites with computed carrying capacity; (c) habitations ranked by urgency from hazard, vulnerability and time-to-impact; (d) assignment within capacity limits, tagged Immediate/Short-term/Medium-term with reasons.

**Pilot selection criteria** `[PROJECT REQUIREMENT]`: multi-hazard; ≥1 documented past event for backtest; open data (terrain, rainfall, roads, villages); a story judges recognise. Candidate districts: Wayanad or Idukki (Kerala), Chamoli/Rudraprayag (Uttarakhand), Kalimpong/Darjeeling (West Bengal), or a coastal taluk for the coastal-erosion layer. Recommended: a landslide+flood district plus a small coastal stretch, so all four named hazards are demonstrated. The final choice is the user's. `[CURRENT ENVIRONMENT FACT]` Existing source access tests used a Bengaluru-area tile — a connectivity test only, not a pilot choice.

**Priority matrix**

| Module | Feature | Priority |
|---|---|---|
| Hazard | Composite per-cell score (slope, rainfall, drainage/flood proximity, LULC, past events), per-factor contributions | Must |
| Hazard | Red Zone classes with adjustable threshold slider | Must |
| Hazard | Rainfall-spike simulator re-scoring landslide+flood (< 5 s) | Must |
| Hazard | Coastal erosion layer (static shoreline-change) | Should |
| Hazard | Backtest of one past event | Should |
| Sites | Candidate screening (slope, hazard, land use, road & water proximity); 3–8 sites with reasons | Must |
| Sites | Multi-resource capacity = min across resources; limiting factor shown | Must |
| Sites | Two tiers: temporary shelters / permanent sites | Should |
| Vulnerability | Index from demographic proxies, editable weights | Must |
| Prioritisation | Urgency = hazard × vulnerability × time factor; ranked table with breakdown | Must |
| Assignment | Greedy with capacity + tie-breaking; reason for each | Must |
| Assignment | Optimal LP and comparison with greedy | Should |
| Assignment | Three-bucket output with documented rules | Must |
| Dashboard | Interactive map, layers, site fill bars, priority table; usable by an outsider | Must |
| Dashboard | What-if controls (site capacity, rainfall, weights) | Should |
| Dashboard | Export action list (PDF/CSV) and GeoJSON | Should |
| Trust | Explanation panel and audit log (top 3 reasons + timestamp) | Should |
| Extras | Multilingual summaries, CAP-style alert drafts (two languages) | Could |


### 7.1 Demo scenario the MVP must support `[PROJECT REQUIREMENT]`

1. **Baseline** — district map with Red Zones and a ranked habitation list.
2. **Explain** — click a village: hazard breakdown, vulnerability profile, urgency score and reasons.
3. **Sites** — candidate sites with capacity and limiting factor (e.g. water).
4. **Trigger** — inject a heavy-rainfall forecast: zones expand, priorities re-rank, villages move into the Immediate bucket.
5. **Conflict** — two villages compete for one nearly full site: show tie-breaking and spill-over to the next site.
6. **Output** — export the action list (buckets, destinations, reasons).

Example reason text format: *"Assigned to Site B because Site A was full after higher-urgency Village 7; Site B is 4.2 km away with water as limiting factor."*

## 8. Functional requirements

**Hazard & zones**
- FR-H1 Compute per-cell hazard scores in [0,1] for landslide and flood; flash-flood/cloudburst as trigger multiplier; coastal erosion as static classes where coastal. (Must)
- FR-H2 Combine: `H = 1 − (1 − H_ls)(1 − H_fl)(1 − H_co)(1 − H_ff)`. (Must)
- FR-H3 Classify Red ≥ 0.7, Amber 0.4–0.7, Green < 0.4; thresholds adjustable live. (Must)
- FR-H4 Separate **structural** zones from **dynamic/Alert** zones driven by rainfall; display both. (Must)
- FR-H5 Show per-factor contributions on click. (Must)

**Habitation**
- FR-V1 Vulnerability index 0–1 from the six proxies, adjustable weights, components visible. (Must)
- FR-U1 Urgency `U = H × (0.5 + V) × T × log(1 + P)`, normalised 0–1. (Must)
- FR-B1 Buckets per §16. (Must)

**Sites**
- FR-S1 Screening per §13. FR-S2 Capacity per §14. FR-S3 Tiering. FR-S4 Fill bars.

**Assignment**
- FR-A1 Greedy; FR-A2 ILP/OR-Tools and comparison; FR-A3 reasons; FR-A4 unassigned reasons.

**Dashboard/Output**
- FR-D1 Map, table, detail panel, status badges. FR-D2 what-if. FR-D3 exports (CSV/PDF/GeoJSON). FR-D4 explanation + audit log. FR-D5 comparison mode: distance-only vs vulnerability-weighted ranking `[PROJECT REQUIREMENT]` (differentiator and value story — Could).

**Data**
- FR-X1 Hybrid ingestion with live/cache/fallback and provenance (see §19, §26).

## 9. Non-functional requirements

NFR-1 Explainability for 100% of assignments `[PROJECT REQUIREMENT]`. NFR-2 Re-rank after rainfall change < 5 s `[PROJECT REQUIREMENT]`. NFR-3 Zero capacity violations `[PROJECT REQUIREMENT]`. NFR-4 Reproducible pipeline (single command rebuilds layers) `[PROJECT REQUIREMENT]`. NFR-5 Pilot-district portability by config `[PROJECT REQUIREMENT]`. NFR-6 Graceful degradation under external failure `[CURRENT ENVIRONMENT FACT]` philosophy. NFR-7 Usability by non-team member unaided `[PROJECT REQUIREMENT]`. NFR-8 Readability on projectors (contrast, large fonts) `[PROJECT REQUIREMENT]`. NFR-9 Mobile-responsive/accessible where feasible `[PROJECT REQUIREMENT]`. NFR-10 Existing environment untouched `[CURRENT ENVIRONMENT FACT]`.

## 10. GIS requirements

- Grid cells 100–250 m aggregated from 30 m rasters, or micro-watersheds `[PROJECT REQUIREMENT]`.
- Storage SRID 4326; metric operations in a district-appropriate projected CRS `[ENGINEERING DECISION]`.
- Mandatory CRS validation before joins; clipping to district boundary; raster alignment to a reference grid.
- Derived terrain: slope, aspect, curvature, drainage/flow accumulation, wetness index, HAND `[PROJECT REQUIREMENT]`.
- GeoJSON outputs; GeoTIFF/GeoPackage for processed rasters/vectors.

## 11. Hazard requirements

Factors `[PROJECT REQUIREMENT]`: landslide — slope, aspect, curvature, geology/soil, distance to drainage, distance to roads, LULC/NDVI, rainfall, past landslide points; flood — HAND, distance to river, flow accumulation, wetness index, rainfall, flood history, LULC; cloudburst/flash flood — catchment steepness + extreme short-duration rainfall (trigger multiplier); coastal erosion — shoreline-change rate, distance to shoreline, coastal slope, protective structures. Methods: weighted overlay (AHP/equal) baseline → frequency ratio or RF/XGBoost with SHAP → rainfall intensity–duration/antecedent rainfall as dynamic trigger. Flood: HAND threshold with rainfall multiplier; satellite flood masks for validation (optional). Missing factors: omit, renormalise, disclose `[ENGINEERING DECISION]`.

## 12. Vulnerability requirements

Proxies: children under 6, aged 60+, persons with disabilities, female-headed households, kutcha houses, distance to nearest health facility. Equal or AHP weights; components shown; weights editable; synthetic components labelled; vulnerability never used to deprioritise anyone `[PROJECT REQUIREMENT]`.

## 13. Relocation-site requirements

Screening (adjustable): outside Red/Amber; slope < ≈15°; land use barren/scrub/government land; within defined distance of all-weather road; within reach of water; not protected forest/wetland `[PROJECT REQUIREMENT]`. Each site stores selection reasons. Sites flagged "screened, not surveyed". Two tiers (temporary shelter outside all Red/Amber zones; permanent/transit).

## 14. Capacity requirements

`C_j = min(C_land, C_water, C_sanitation, C_road, C_services)` with the limiting factor reported `[PROJECT REQUIREMENT]`. Norms configurable, cited, versioned (Sphere-style for temporary; state housing norms for permanent). `[ENGINEERING DECISION]` No numeric norm may be silently invented; unsourced values are flagged placeholders. Confidence level (low/medium/high) per site. Supports what-if changes to site size (e.g. −30%).

## 15. Risk / urgency scoring requirements

Formula §8 FR-U1. T ∈ [1.0, ≈1.5]: 1.0 at baseline, increasing as forecast trigger nears or recent failure/flood recorded `[PROJECT REQUIREMENT]`; the concrete mapping is `[ENGINEERING DECISION]`, configurable and displayed. Per-term breakdown stored and shown.

## 16. Time-bucket requirements `[PROJECT REQUIREMENT]` (configurable)

Immediate: U ≥ 0.75 or H ≥ 0.85 with active alert → temporary shelters. Short-term: 0.45 ≤ U < 0.75 → permanent/transit sites. Medium-term: U < 0.45 inside a structural Red Zone → permanent sites. `[ENGINEERING DECISION]` Else `NONE/monitor`.

## 17. Assignment requirements

Greedy: sort by U (ties: higher V → larger P → closer site); eligible = correct tier, within distance limit, remaining capacity ≥ demand; assign nearest; split by household groups or mark unassigned with reason. ILP: maximise Σ(U_iP_i − λ d_ij P_i)x_ij with the three constraints above; report improvement over greedy `[PROJECT REQUIREMENT]`. Invariants: no site over capacity; every habitation assigned or has reason; deterministic. Distance `d_ij` via road graph with straight-line fallback `[ENGINEERING DECISION]`.

## 18. Explainability requirements

Per-factor hazard contributions; urgency term breakdown; vulnerability components; per-assignment decision path and one-sentence reason; top three reasons + timestamp; audit log (user, action, before/after, timestamp); adjustable weights/thresholds visible `[PROJECT REQUIREMENT]`. Reasons are templated from deterministic values; an LLM may only paraphrase `[OPTIONAL FUTURE ENHANCEMENT]`.

## 19. Data-source requirements

| Layer | Source | Status |
|---|---|---|
| Rainfall | NASA GPM IMERG (near-real-time via PPS) | `[CURRENT ENVIRONMENT FACT]` auth configured & tested — **preserve** |
| Elevation | Copernicus DEM GLO-30 (public S3) | verified access |
| Land cover | ESA WorldCover 2021 v200 (public S3) | verified access |
| Roads/water/health | OSM: LIVE → CACHE → regional `.osm.pbf` | extract **not yet downloaded** (pilot pending) |
| Event inventory | GSI/NASA catalog/news-derived/SDMA | to source for pilot `[PROJECT REQUIREMENT]` |
| Demographics | Census 2011 / WorldPop / synthetic | synthetic labelled |
| Coastal | NCCR/Sentinel-derived shorelines | optional for coastal stretch |

Other sources (additional alternatives, not requirements: IMD gridded rainfall, ERA5, Bhuvan, India-WRIS, SoilGrids, Google/Microsoft buildings, SVAMITVA) are optional alternatives, not requirements. Record licence and access date for each dataset `[PROJECT REQUIREMENT]`. Principle: REAL FIRST → CACHED → INTELLIGENT FALLBACK → NEVER FAKE LIVE.

## 20. Data-quality requirements

CRS validated; nodata explicit; value-range checks; checksum + manifest; origin label (LIVE/CACHED/DEMO_SYNTHETIC) on every dataset and row-set; derived data inherits weakest origin; synthetic generators seeded and documented; uncertainty shown (low/med/high); stale data flagged; honest limitations page (synthetic demographics, screened sites, static shoreline, single-district validation) `[PROJECT REQUIREMENT]`.

## 21. API requirements

See APP_FLOW §20. FastAPI, versioned `/api/v1`, Pydantic models, GeoJSON for spatial data, provenance envelope on every data response, uniform error format, `/health` and `/health/db` unchanged. No secrets in responses. Scenario runs non-destructive.

## 22. Frontend requirements

React + TypeScript + Vite + MapLibre (+ Turf, Recharts, Axios, React Router, Lucide) — existing stack only. Views: dashboard (map, layer toggles, threshold slider, rainfall-spike control, priority table, site fill bars, detail/explanation panel), scenario compare, validation (backtest/ROC, sensitivity), data-status, about/assumptions. Data-status badges everywhere. High-contrast, large fonts. One-click reset of scenario. Exports. No secrets, no direct external calls.

## 23. Database schema requirements

PostgreSQL 17 / PostGIS 3.6.2, DB `surakshit_basti`; migrations for all changes; SRID 4326 + GiST. Entities `[PROJECT REQUIREMENT]`:
- **Cell**: id, geometry, factor values, hazard scores per type, combined score, class, timestamp
- **Habitation**: id, name, geometry, population, households, vulnerability components, hazard score, urgency, bucket, assigned site, reason
- **Site**: id, name, geometry, tier, area, resource capacities, final capacity, limiting factor, allocated, remaining
- **Event**: id, type, date, location, source
- **Scenario**: id, rainfall multiplier, weight settings, site adjustments, results snapshot
- **Audit log**: id, user, action, before/after, timestamp

`[ENGINEERING DECISION]` Plus: `districts`, `datasets`, `ingestion_runs`, `rainfall_observations`, `assignments`, `capacity_norms`; every ingested/derived row has `data_origin`, `source`, `retrieved_at`. `mcp_readonly` keeps SELECT only.

## 24. Security requirements

Secrets only in `.env` (never committed/printed/logged/frontend/API); PPS credentials server-side only; parameterised SQL; input validation; CORS restricted; no stack traces to clients; audit log; human override. Presence-only checks of secrets.

## 25. Performance requirements

Rainfall-spike re-rank < 5 s `[PROJECT REQUIREMENT]`; precomputed structural layers and distance matrix `[ENGINEERING DECISION]`; map layers bbox-filtered; assignment solver time-limited with greedy fallback; pilot sized for hundreds of habitations (stress test with shrinking capacity). Other latency targets are proposed, to be measured in Phase 11: p95 read endpoints < 1 s on pilot data.

## 26. Failure / fallback requirements

Per APP_FLOW §19. Summary: IMERG failure → cached rainfall → `UNAVAILABLE` dynamic layer (structural zones remain; simulator works, labelled SIMULATED). Overpass failure → cached OSM → `.osm.pbf` extract → straight-line fallback (labelled). DEM/WorldCover → local raw files. Solver failure → greedy. Never crash on external outage; never relabel CACHED as LIVE; never silently use synthetic.

## 27. Testing requirements `[PROJECT REQUIREMENT]`

Unit tests for each factor, score range, bucket rule; property tests (no over-capacity; assigned-or-reason); randomised stress tests (hundreds of habitations, shrinking capacity); sensitivity (±20% weights → rank changes); backtest ≥1 documented event; API tests; ingestion tests with mocked network; CRS-mismatch tests; frontend build/lint.

## 28. Acceptance criteria

| # | Criterion | Source |
|---|---|---|
| AC1 | Existing baseline checklist (AGENTS §0.1) green after every phase | ENV |
| AC2 | Hazard score in [0,1] with per-factor contribution on click | PROJECT REQ |
| AC3 | Red threshold slider changes map live | PROJECT REQ |
| AC4 | Rainfall spike changes zones and ranks in < 5 s | PROJECT REQ |
| AC5 | 3–8 candidate sites, each with reasons and capacity + limiting factor | PROJECT REQ |
| AC6 | Vulnerability index per habitation with editable weights | PROJECT REQ |
| AC7 | Ranked urgency table with breakdown | PROJECT REQ |
| AC8 | Zero capacity violations across ≥1,000 randomised runs | PROJECT REQ |
| AC9 | 100% of assignments carry reasons; unassigned have reasons | PROJECT REQ |
| AC10 | Every habitation tagged with a bucket per documented rules | PROJECT REQ |
| AC11 | Greedy vs optimal comparison shown | PROJECT REQ (Should) |
| AC12 | Hazard model AUC ≥ ~0.75–0.85 on held-out events (data permitting) | PROJECT REQ |
| AC13 | One backtested event flagged before event date | PROJECT REQ (Should) |
| AC14 | Outsider completes the demo tasks unaided | PROJECT REQ |
| AC15 | All data labelled LIVE/CACHED/DEMO_SYNTHETIC with timestamps | ENV |
| AC16 | OSM ladder works: simulated Overpass failure falls to cache then extract | ENV |
| AC17 | No secrets in repo, logs, responses, or frontend bundle | ENV |
| AC18 | Switching pilot district requires config/data change only | PROJECT REQ |
| AC19 | Export produces CSV/GeoJSON (PDF Should) with buckets, destinations, reasons | PROJECT REQ |

Success metrics `[PROJECT REQUIREMENT]`: AUC; backtest lead; zero violations; 100% explainability; < 5 s re-rank; unaided usability.

## 29. Future enhancements `[OPTIONAL FUTURE ENHANCEMENT]`

Multilingual summaries and CAP-style alert drafts (Could); 3D terrain view; cost/timeline estimator; LLM-drafted action briefs (numbers from engines only); offline field verification form; additional hazards (earthquake, GLOF, cyclone surge, subsidence); live IMD feeds; NDEM/Bhuvan/SACHET/PM Gati Shakti/SVAMITVA integrations; role-based access and approval workflows; vector tiles; Earth Engine / cloud-native architecture; state-level scale.

## 30. Out-of-scope items `[PROJECT REQUIREMENT]` + `[CURRENT ENVIRONMENT FACT]`

National coverage; real-time government pipeline integrations; mobile field apps; legal/land-title/compensation workflows; detailed site engineering design; enterprise infrastructure (Kubernetes, microservices, message brokers); MCP as an application dependency; Celery/Redis for MVP `[ENGINEERING DECISION]`.

---

## Assumptions & ambiguities log

| # | Ambiguity | Safest assumption `[ENGINEERING DECISION]` |
|---|---|---|
| A1 | Pilot district not chosen; environment tests used Bengaluru tiles | Treat Bengaluru as plumbing test; select hazard-bearing pilot (PRD §7 criteria) before heavy ingestion/OSM extract download |
| A2 | A task queue (Celery/Redis) is a common option but is not installed | Skip for MVP; use scripts + background tasks |
| A3 | Normalisation method for U not specified | Min–max within scenario; documented and configurable |
| A4 | Mapping for T not specified | Linear 1.0→1.5 on trigger ratio/recent-event recency; configurable |
| A5 | Bucket for U < 0.45 outside structural Red Zone | `NONE/monitor` |
| A6 | λ in ILP objective not specified | Configurable; tuned with user after sensitivity runs |
| A7 | Capacity numeric norms not given | Cited configurable norms; placeholders flagged until sourced |
| A8 | Habitation hazard inheritance from cells | Max cell hazard under footprint (configurable) |
| A9 | "Route optimization engine" in architecture but not named in the MVP feature list | Implement as road-graph `d_ij` + eligibility with straight-line fallback; no turn-by-turn routing |
| A10 | Government-owned land can't be inferred from open data | Use land-cover proxy; labelled assumption |