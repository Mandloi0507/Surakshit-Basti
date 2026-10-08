"""
Assignment service: orchestrates the full relocation assignment pipeline.

Pipeline:
1. Load habitations (with urgency scores) and sites (with capacity) from DB
2. Compute distance matrix
3. Run greedy and/or ILP solver
4. Create scenario record
5. Persist assignments to DB
6. Update habitation.assigned_site_id and site.allocated_population
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from backend.app.core.logging import get_logger
from backend.app.database import SessionLocal
from backend.app.engines.assignment_engine import (
    AssignmentResult,
    AssignmentSolution,
    HabitationDemand,
    SiteSupply,
    greedy_assign,
    ilp_assign,
    validate_assignment_invariants,
)
from backend.app.engines.routing_engine import (
    LocationPoint,
    compute_distance_matrix,
)
from backend.app.models.assignment import Assignment
from backend.app.models.habitation import Habitation
from backend.app.models.scenario import Scenario
from backend.app.models.site import Site

logger = get_logger(__name__)


def _load_habitations_and_sites(
    district_id: str,
    session: Session,
) -> Tuple[List[Habitation], List[Site]]:
    """Load habitations and sites from DB for a district."""
    habitations = (
        session.query(Habitation)
        .filter(Habitation.district_id == district_id)
        .order_by(Habitation.urgency_score.desc())
        .all()
    )
    sites = (
        session.query(Site)
        .filter(Site.district_id == district_id)
        .order_by(Site.final_capacity.desc())
        .all()
    )
    return habitations, sites


def run_assignment_pipeline(
    district_id: str,
    scenario_id: str,
    scenario_name: str,
    solver_method: str = "greedy",
    rainfall_multiplier: float = 1.0,
    weight_overrides: Optional[Dict] = None,
    site_adjustments: Optional[Dict] = None,
    max_distance_km: float = 50.0,
    db: Optional[Session] = None,
) -> AssignmentSolution:
    """
    Run the full assignment pipeline for a district + scenario.

    Steps:
    1. Load habitations and sites from the DB
    2. Build demands and supplies
    3. Compute distance matrix
    4. Run assignment solver
    5. Validate invariants
    6. Persist scenario + assignments to DB
    7. Update habitation.assigned_site_id and site allocations

    Returns:
        AssignmentSolution with all assignments, stats, and invariant validation.
    """
    session = db or SessionLocal()
    should_close = db is None

    try:
        # 1. Load from DB
        hab_models, site_models = _load_habitations_and_sites(district_id, session)
        if not hab_models:
            raise ValueError(f"No habitations found for district={district_id}. Run demo seed first.")
        if not site_models:
            raise ValueError(f"No sites found for district={district_id}. Run demo seed first.")

        logger.info(
            "Assignment pipeline: %d habitations, %d sites for district=%s",
            len(hab_models), len(site_models), district_id,
        )

        # 2. Build demands and supplies
        demands: List[HabitationDemand] = []
        hab_locations: List[LocationPoint] = []
        for h in hab_models:
            shape = to_shape(h.geometry)
            demands.append(HabitationDemand(
                id=h.id,
                population=h.population,
                urgency_score=h.urgency_score,
                vulnerability_index=h.vulnerability_index,
                bucket=h.bucket,
            ))
            hab_locations.append(LocationPoint(id=h.id, lat=shape.y, lon=shape.x))

        supplies: List[SiteSupply] = []
        site_locations: List[LocationPoint] = []
        for s in site_models:
            shape = to_shape(s.geometry)
            supplies.append(SiteSupply(
                id=s.id,
                tier=s.tier,
                final_capacity=s.final_capacity,
                remaining_capacity=s.final_capacity,  # Reset for this scenario
            ))
            site_locations.append(LocationPoint(id=s.id, lat=shape.y, lon=shape.x))

        # 3. Compute distance matrix
        dist_result = compute_distance_matrix(hab_locations, site_locations)
        logger.info(
            "Distance matrix: %s × %s, method=%s",
            dist_result.distances_km.shape[0], dist_result.distances_km.shape[1],
            dist_result.routing_method,
        )

        # 4. Run solver
        if solver_method == "ilp_ortools":
            solution = ilp_assign(
                demands, supplies, dist_result.distances_km,
                routing_method=dist_result.routing_method,
                max_distance_km=max_distance_km,
            )
        else:
            solution = greedy_assign(
                demands, supplies, dist_result.distances_km,
                routing_method=dist_result.routing_method,
                max_distance_km=max_distance_km,
            )

        # 5. Validate invariants
        violations = validate_assignment_invariants(solution, supplies)
        if violations:
            logger.error("Assignment invariant violations: %s", violations)
            solution.stats["invariant_violations"] = violations
        else:
            logger.info("All assignment invariants satisfied.")
            solution.stats["invariant_violations"] = []

        # 6. Persist scenario + assignments to DB
        # Delete existing scenario + assignments if re-running
        existing_scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if existing_scenario:
            session.query(Assignment).filter(Assignment.scenario_id == scenario_id).delete()
            session.delete(existing_scenario)
            session.flush()

        scenario = Scenario(
            id=scenario_id,
            district_id=district_id,
            name=scenario_name,
            description=f"Assignment run with {solution.solver_method} solver",
            rainfall_multiplier=rainfall_multiplier,
            weight_overrides_json=weight_overrides or {},
            site_adjustments_json=site_adjustments or {},
            is_active=True,
        )
        session.add(scenario)
        session.flush()

        for a in solution.assignments:
            assignment = Assignment(
                id=f"asgn_{scenario_id}_{a.habitation_id}",
                scenario_id=scenario_id,
                habitation_id=a.habitation_id,
                site_id=a.site_id,
                assigned_population=a.assigned_population,
                distance_km=a.distance_km,
                routing_method=a.routing_method,
                decision_rank=a.decision_rank,
                reasons_json=a.reasons,
                unassigned_reason=a.unassigned_reason,
                solver_method=a.solver_method,
            )
            session.add(assignment)

        # 7. Update habitation.assigned_site_id and site allocations
        site_allocations: Dict[str, int] = {}
        for a in solution.assignments:
            if a.site_id:
                site_allocations[a.site_id] = (
                    site_allocations.get(a.site_id, 0) + a.assigned_population
                )

            # Update habitation snapshot
            hab_obj = session.query(Habitation).filter(Habitation.id == a.habitation_id).first()
            if hab_obj:
                hab_obj.assigned_site_id = a.site_id
                hab_obj.unassigned_reason = a.unassigned_reason
                hab_obj.decision_reasons_json = {
                    "scenario_id": scenario_id,
                    "solver": a.solver_method,
                    "rank": a.decision_rank,
                    "reasons": a.reasons,
                    "unassigned_reason": a.unassigned_reason,
                }

        # Update site allocation counts
        for site_obj in site_models:
            allocated = site_allocations.get(site_obj.id, 0)
            site_obj.allocated_population = allocated
            site_obj.remaining_capacity = site_obj.final_capacity - allocated

        session.commit()
        logger.info(
            "Assignment pipeline complete: %d assigned, %d unassigned, solver=%s",
            solution.total_assigned, solution.total_unassigned, solution.solver_method,
        )

        return solution

    except Exception:
        session.rollback()
        logger.exception("Assignment pipeline failed for district=%s, scenario=%s", district_id, scenario_id)
        raise
    finally:
        if should_close:
            session.close()
