# Assumptions

## Phase 4 Terrain And Hazard Processing

- `[ENGINEERING DECISION]` `hazard_engine.py` accepts district YAML factor-weight names and canonical engine names. Positive weights are renormalised before weighted overlay so omitted factors do not silently inflate or deflate hazard scores.
- `[ENGINEERING DECISION]` `cells.structural_hazard` stores terrain/static hazard separately from `cells.combined_hazard`, which may include rainfall-triggered dynamic expansion.
- `[ENGINEERING DECISION]` `hazard_service.generate_district_cell_grid()` currently creates deterministic demo cells from district bbox coordinates until raster-derived processed layers are wired in. Those rows are labelled `DEMO_SYNTHETIC`, never `LIVE` or `CACHED`.

## Phase 5 Habitations, Vulnerability, Urgency, And Buckets

- `[ENGINEERING DECISION]` Vulnerability uses the six PRD proxies with configurable positive weights renormalised to sum to one. Health-facility distance is normalised against 10 km until a district-specific service-access threshold is provided.
- `[ENGINEERING DECISION]` Urgency raw scores use the PRD formula exactly, then min-max normalise across the active scenario's habitations.
- `[ENGINEERING DECISION]` `time_factors.baseline=1.0`, `time_factors.active_alert=1.5`, and `time_factors.recent_event=1.25` are configurable district defaults.
- `[ENGINEERING DECISION]` Demo habitations are seeded, deterministic, and labelled `DEMO_SYNTHETIC`; they are placeholders until real habitation geometry and demographics are loaded.
