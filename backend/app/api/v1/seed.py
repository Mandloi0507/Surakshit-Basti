"""
Seed API router: populates demo synthetic data for testing and presentations.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.assignment_service import run_assignment_pipeline
from backend.app.services.habitation_service import populate_demo_habitations_in_db
from backend.app.services.hazard_service import populate_district_cells_in_db
from backend.app.services.site_service import populate_demo_sites_in_db

router = APIRouter(prefix="/seed", tags=["Demo Seeding"])


@router.post("/demo", response_model=Dict[str, Any])
def seed_demo_data(
    district_id: str = Query("wayanad", description="District identifier"),
    habitations_count: int = Query(10, ge=1, le=50),
    sites_count: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Populate complete demo dataset for a district:
    - 1 km grid terrain cells with multi-hazard scores
    - Habitations with vulnerability and urgency scores
    - Candidate relocation sites with screening and capacity norms
    - Baseline relocation scenario execution (Greedy and ILP)
    """
    n_cells = populate_district_cells_in_db(district_id, db=db)
    n_habs = populate_demo_habitations_in_db(district_id, count=habitations_count, db=db)
    n_sites = populate_demo_sites_in_db(district_id, count=sites_count, db=db)

    # Run baseline scenario
    solution = run_assignment_pipeline(
        district_id=district_id,
        scenario_id=f"scen_{district_id}_baseline",
        scenario_name=f"Baseline {district_id.title()} Relocation Plan",
        solver_method="greedy",
        db=db,
    )

    return {
        "status": "success",
        "district_id": district_id,
        "cells_populated": n_cells,
        "habitations_populated": n_habs,
        "sites_populated": n_sites,
        "baseline_scenario_id": f"scen_{district_id}_baseline",
        "assigned_count": solution.total_assigned,
        "unassigned_count": solution.total_unassigned,
    }
