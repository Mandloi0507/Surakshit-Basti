"""
Scenarios API router: create, run, and compare what-if relocation scenarios.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.scenario import Scenario
from backend.app.schemas.scenario import ScenarioBase, ScenarioOut
from backend.app.services.scenario_service import compare_scenarios, simulate_what_if_scenario

router = APIRouter(prefix="/scenarios", tags=["Scenarios & What-If"])


class ScenarioRunRequest(BaseModel):
    district_id: str = "wayanad"
    name: str = "Custom What-If Scenario"
    rainfall_multiplier: float = Field(1.0, ge=0.5, le=5.0)
    solver_method: str = Field("greedy", pattern="^(greedy|ilp_ortools)$")
    weight_overrides: Optional[Dict[str, float]] = None
    site_adjustments: Optional[Dict[str, int]] = None


@router.get("", response_model=List[ScenarioOut])
def list_scenarios(
    district_id: str = Query("wayanad", description="District identifier"),
    db: Session = Depends(get_db),
):
    """
    List all scenarios evaluated for a district.
    """
    scenarios = (
        db.query(Scenario)
        .filter(Scenario.district_id == district_id)
        .order_by(Scenario.created_at.desc())
        .all()
    )
    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
):
    """
    Get metadata for a specific scenario.
    """
    scen = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen


@router.post("/run", response_model=Dict[str, Any])
def run_scenario(
    req: ScenarioRunRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate and execute relocation assignment for a scenario.
    Runs hazard/urgency re-computation and solver optimization.
    """
    result = simulate_what_if_scenario(
        district_id=req.district_id,
        scenario_name=req.name,
        rainfall_multiplier=req.rainfall_multiplier,
        solver_method=req.solver_method,
        weight_overrides=req.weight_overrides,
        site_adjustments=req.site_adjustments,
        db=db,
    )
    return result


@router.get("/{scenario_id}/compare/{other_scenario_id}", response_model=Dict[str, Any])
def compare_two_scenarios(
    scenario_id: str,
    other_scenario_id: str,
    db: Session = Depends(get_db),
):
    """
    Compare two scenarios side by side (shifts in habitations, population, capacities).
    """
    return compare_scenarios(scenario_id, other_scenario_id, db=db)
