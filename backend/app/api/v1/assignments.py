"""
Assignments API router: query relocation assignments, export to CSV and GeoJSON.
"""
import csv
import io
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from geoalchemy2.shape import to_shape
from shapely.geometry import LineString, mapping
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.assignment import Assignment
from backend.app.models.habitation import Habitation
from backend.app.models.site import Site
from backend.app.schemas.assignment import AssignmentBase, AssignmentOut

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("", response_model=List[AssignmentOut])
def get_assignments(
    scenario_id: str = Query(..., description="Scenario identifier"),
    db: Session = Depends(get_db),
):
    """
    Get all assignment rows for a specific scenario run.
    """
    assignments = (
        db.query(Assignment)
        .filter(Assignment.scenario_id == scenario_id)
        .order_by(Assignment.decision_rank.asc())
        .all()
    )
    return assignments


@router.get("/export/csv")
def export_assignments_csv(
    scenario_id: str = Query(..., description="Scenario identifier"),
    db: Session = Depends(get_db),
):
    """
    Export assignments as a downloadable CSV for emergency officers / district administration.
    """
    assignments = (
        db.query(Assignment)
        .filter(Assignment.scenario_id == scenario_id)
        .order_by(Assignment.decision_rank.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Decision Rank",
        "Habitation ID",
        "Assigned Site ID",
        "Assigned Population",
        "Distance (km)",
        "Routing Method",
        "Solver Method",
        "Unassigned Reason",
        "Decision Reasons",
    ])

    for a in assignments:
        reasons_str = " | ".join(a.reasons_json) if a.reasons_json else ""
        writer.writerow([
            a.decision_rank,
            a.habitation_id,
            a.site_id or "UNASSIGNED",
            a.assigned_population,
            f"{a.distance_km:.2f}",
            a.routing_method,
            a.solver_method,
            a.unassigned_reason or "N/A",
            reasons_str,
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=assignments_{scenario_id}.csv"
        },
    )


@router.get("/export/geojson", response_model=Dict[str, Any])
def export_assignments_geojson(
    scenario_id: str = Query(..., description="Scenario identifier"),
    db: Session = Depends(get_db),
):
    """
    Returns GeoJSON FeatureCollection of connection flow lines between habitations and assigned sites.
    """
    assignments = (
        db.query(Assignment)
        .filter(Assignment.scenario_id == scenario_id, Assignment.site_id.isnot(None))
        .all()
    )

    features = []
    for a in assignments:
        hab = db.query(Habitation).filter(Habitation.id == a.habitation_id).first()
        site = db.query(Site).filter(Site.id == a.site_id).first()

        if hab and site:
            hab_pt = to_shape(hab.geometry)
            site_pt = to_shape(site.geometry)
            line = LineString([(hab_pt.x, hab_pt.y), (site_pt.x, site_pt.y)])

            features.append({
                "type": "Feature",
                "id": a.id,
                "geometry": mapping(line),
                "properties": {
                    "habitation_id": a.habitation_id,
                    "habitation_name": hab.name,
                    "site_id": a.site_id,
                    "site_name": site.name,
                    "assigned_population": a.assigned_population,
                    "distance_km": a.distance_km,
                    "decision_rank": a.decision_rank,
                },
            })

    return {
        "type": "FeatureCollection",
        "scenario_id": scenario_id,
        "total_flows": len(features),
        "features": features,
    }
