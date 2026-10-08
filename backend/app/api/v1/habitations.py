"""
Habitations API router: GeoJSON and priority list endpoints for disaster-prone habitations.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.habitation import Habitation
from backend.app.schemas.habitation import HabitationBase, HabitationOut

router = APIRouter(prefix="/habitations", tags=["Habitations"])


@router.get("", response_model=Dict[str, Any])
def get_habitations_geojson(
    district_id: str = Query("wayanad", description="District identifier"),
    bucket: Optional[str] = Query(None, description="Filter by Immediate, Short-term, Medium-term, NONE"),
    db: Session = Depends(get_db),
):
    """
    Returns GeoJSON FeatureCollection of all habitations with vulnerability and urgency properties.
    """
    query = db.query(Habitation).filter(Habitation.district_id == district_id)
    if bucket:
        query = query.filter(Habitation.bucket == bucket)

    habs = query.order_by(Habitation.urgency_score.desc()).all()

    features = []
    for h in habs:
        geom_shape = to_shape(h.geometry)
        props = {
            "id": h.id,
            "district_id": h.district_id,
            "name": h.name,
            "population": h.population,
            "households": h.households,
            "vuln_children_u6": h.vuln_children_u6,
            "vuln_elderly_60p": h.vuln_elderly_60p,
            "vuln_disabled": h.vuln_disabled,
            "vuln_female_head": h.vuln_female_head,
            "vuln_kutcha": h.vuln_kutcha,
            "vuln_dist_health_m": h.vuln_dist_health_m,
            "vulnerability_index": h.vulnerability_index,
            "hazard_score": h.hazard_score,
            "structural_hazard": h.structural_hazard,
            "time_factor": h.time_factor,
            "raw_urgency_score": h.raw_urgency_score,
            "urgency_score": h.urgency_score,
            "bucket": h.bucket,
            "vulnerability_breakdown_json": h.vulnerability_breakdown_json or {},
            "urgency_breakdown_json": h.urgency_breakdown_json or {},
            "assigned_site_id": h.assigned_site_id,
            "unassigned_reason": h.unassigned_reason,
            "decision_reasons_json": h.decision_reasons_json or {},
            "data_origin": h.data_origin,
        }
        features.append({
            "type": "Feature",
            "id": h.id,
            "geometry": mapping(geom_shape),
            "properties": props,
        })

    return {
        "type": "FeatureCollection",
        "total_count": len(features),
        "district_id": district_id,
        "features": features,
    }


@router.get("/priority-table", response_model=List[HabitationBase])
def get_priority_table(
    district_id: str = Query("wayanad", description="District identifier"),
    db: Session = Depends(get_db),
):
    """
    Returns priority-sorted list of habitations ordered by Urgency Score descending.
    """
    habs = (
        db.query(Habitation)
        .filter(Habitation.district_id == district_id)
        .order_by(Habitation.urgency_score.desc(), Habitation.population.desc())
        .all()
    )
    return [
        HabitationBase(
            id=h.id,
            district_id=h.district_id,
            name=h.name,
            population=h.population,
            households=h.households,
            vuln_children_u6=h.vuln_children_u6,
            vuln_elderly_60p=h.vuln_elderly_60p,
            vuln_disabled=h.vuln_disabled,
            vuln_female_head=h.vuln_female_head,
            vuln_kutcha=h.vuln_kutcha,
            vuln_dist_health_m=h.vuln_dist_health_m,
            vulnerability_index=h.vulnerability_index,
            hazard_score=h.hazard_score,
            structural_hazard=h.structural_hazard,
            time_factor=h.time_factor,
            raw_urgency_score=h.raw_urgency_score,
            urgency_score=h.urgency_score,
            bucket=h.bucket,
            vulnerability_breakdown_json=h.vulnerability_breakdown_json or {},
            urgency_breakdown_json=h.urgency_breakdown_json or {},
            assigned_site_id=h.assigned_site_id,
            unassigned_reason=h.unassigned_reason,
            decision_reasons_json=h.decision_reasons_json or {},
            data_origin=h.data_origin,
        )
        for h in habs
    ]


@router.get("/{habitation_id}", response_model=HabitationBase)
def get_habitation_detail(
    habitation_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns detailed habitation object with explainable vulnerability and urgency breakdown.
    """
    h = db.query(Habitation).filter(Habitation.id == habitation_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Habitation not found")

    return HabitationBase(
        id=h.id,
        district_id=h.district_id,
        name=h.name,
        population=h.population,
        households=h.households,
        vuln_children_u6=h.vuln_children_u6,
        vuln_elderly_60p=h.vuln_elderly_60p,
        vuln_disabled=h.vuln_disabled,
        vuln_female_head=h.vuln_female_head,
        vuln_kutcha=h.vuln_kutcha,
        vuln_dist_health_m=h.vuln_dist_health_m,
        vulnerability_index=h.vulnerability_index,
        hazard_score=h.hazard_score,
        structural_hazard=h.structural_hazard,
        time_factor=h.time_factor,
        raw_urgency_score=h.raw_urgency_score,
        urgency_score=h.urgency_score,
        bucket=h.bucket,
        vulnerability_breakdown_json=h.vulnerability_breakdown_json or {},
        urgency_breakdown_json=h.urgency_breakdown_json or {},
        assigned_site_id=h.assigned_site_id,
        unassigned_reason=h.unassigned_reason,
        decision_reasons_json=h.decision_reasons_json or {},
        data_origin=h.data_origin,
    )
