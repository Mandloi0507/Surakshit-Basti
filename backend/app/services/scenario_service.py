"""
Scenario service: handles what-if scenario simulations, dynamic hazard/urgency re-scoring,
and scenario-to-scenario comparisons for decision support.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.database import SessionLocal
from backend.app.engines.urgency_engine import UrgencyInput, normalize_urgency_scores
from backend.app.models.assignment import Assignment
from backend.app.models.habitation import Habitation
from backend.app.models.scenario import Scenario
from backend.app.models.site import Site
from backend.app.services.assignment_service import run_assignment_pipeline

logger = get_logger(__name__)


def simulate_what_if_scenario(
    district_id: str,
    scenario_name: str,
    rainfall_multiplier: float = 1.0,
    solver_method: str = "greedy",
    weight_overrides: Optional[Dict[str, float]] = None,
    site_adjustments: Optional[Dict[str, int]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Run dynamic What-If simulation:
    1. If rainfall_multiplier != 1.0, adjust effective hazard score for habitations
    2. Re-compute urgency scores and buckets
    3. Run assignment solver
    4. Return full solution and scenario metadata in < 5 seconds
    """
    session = db or SessionLocal()
    should_close = db is None

    try:
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        district: DistrictConfig = load_district_config(district_id)

        # 1. If rainfall multiplier or weight overrides provided, temporarily adjust habitations
        hab_models = (
            session.query(Habitation)
            .filter(Habitation.district_id == district_id)
            .all()
        )

        if not hab_models:
            raise ValueError(f"No habitations found for district {district_id}. Please seed data first.")

        # Re-score urgency with rainfall multiplier
        urgency_inputs = []
        for h in hab_models:
            # Multiplier directly amplifies hazard score (capped at 1.0)
            effective_hazard = min(1.0, h.structural_hazard * rainfall_multiplier)
            time_factor = district.time_factors.active_alert if rainfall_multiplier > 1.2 else district.time_factors.baseline

            urgency_inputs.append(
                UrgencyInput(
                    id=h.id,
                    hazard_score=effective_hazard,
                    structural_hazard=h.structural_hazard,
                    vulnerability_index=h.vulnerability_index,
                    time_factor=time_factor,
                    population=h.population,
                    active_alert=(rainfall_multiplier > 1.2),
                )
            )

        urgency_results = normalize_urgency_scores(
            urgency_inputs,
            immediate_min=district.thresholds.immediate_urgency_min,
            short_term_min=district.thresholds.short_term_urgency_min,
            red_zone_min=district.thresholds.red_zone_min,
        )
        urgency_map = {res.id: res for res in urgency_results}

        # Update in-memory / DB for this district run
        for h in hab_models:
            res = urgency_map[h.id]
            h.hazard_score = min(1.0, h.structural_hazard * rainfall_multiplier)
            h.raw_urgency_score = res.raw_urgency
            h.urgency_score = res.urgency_score
            h.bucket = res.bucket
            h.urgency_breakdown_json = res.breakdown

        session.flush()

        # 2. Run assignment pipeline
        solution = run_assignment_pipeline(
            district_id=district_id,
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            solver_method=solver_method,
            rainfall_multiplier=rainfall_multiplier,
            weight_overrides=weight_overrides,
            site_adjustments=site_adjustments,
            db=session,
        )

        return {
            "scenario_id": scenario_id,
            "name": scenario_name,
            "district_id": district_id,
            "rainfall_multiplier": rainfall_multiplier,
            "solver_method": solver_method,
            "total_assigned": solution.total_assigned,
            "total_unassigned": solution.total_unassigned,
            "stats": solution.stats,
            "assignments_count": len(solution.assignments),
            "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
        }
    except Exception:
        session.rollback()
        logger.exception("Failed to simulate what-if scenario for district=%s", district_id)
        raise
    finally:
        if should_close:
            session.close()


def compare_scenarios(
    scenario_id_1: str,
    scenario_id_2: str,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Compare two scenarios side-by-side:
    - Overall metrics: total assigned, unassigned, population displaced
    - Habitation assignment shifts (site changes, bucket changes)
    - Site capacity changes
    """
    session = db or SessionLocal()
    should_close = db is None

    try:
        s1 = session.query(Scenario).filter(Scenario.id == scenario_id_1).first()
        s2 = session.query(Scenario).filter(Scenario.id == scenario_id_2).first()

        if not s1 or not s2:
            raise ValueError("One or both scenarios not found.")

        asgns_1 = session.query(Assignment).filter(Assignment.scenario_id == scenario_id_1).all()
        asgns_2 = session.query(Assignment).filter(Assignment.scenario_id == scenario_id_2).all()

        map1 = {a.habitation_id: a for a in asgns_1}
        map2 = {a.habitation_id: a for a in asgns_2}

        all_hab_ids = set(map1.keys()) | set(map2.keys())
        shifts = []

        for hid in sorted(all_hab_ids):
            a1 = map1.get(hid)
            a2 = map2.get(hid)
            site1 = a1.site_id if a1 else None
            site2 = a2.site_id if a2 else None

            if site1 != site2:
                shifts.append({
                    "habitation_id": hid,
                    "scenario_1_site": site1,
                    "scenario_2_site": site2,
                    "scenario_1_distance_km": a1.distance_km if a1 else 0.0,
                    "scenario_2_distance_km": a2.distance_km if a2 else 0.0,
                })

        return {
            "scenario_1": {
                "id": s1.id,
                "name": s1.name,
                "rainfall_multiplier": s1.rainfall_multiplier,
                "total_assigned": sum(1 for a in asgns_1 if a.site_id),
                "total_unassigned": sum(1 for a in asgns_1 if not a.site_id),
                "total_population_relocated": sum(a.assigned_population for a in asgns_1),
            },
            "scenario_2": {
                "id": s2.id,
                "name": s2.name,
                "rainfall_multiplier": s2.rainfall_multiplier,
                "total_assigned": sum(1 for a in asgns_2 if a.site_id),
                "total_unassigned": sum(1 for a in asgns_2 if not a.site_id),
                "total_population_relocated": sum(a.assigned_population for a in asgns_2),
            },
            "shift_count": len(shifts),
            "shifts": shifts,
            "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
        }
    finally:
        if should_close:
            session.close()
