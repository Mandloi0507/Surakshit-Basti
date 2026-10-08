"""
Sites API router: candidate relocation sites with multi-resource carrying capacity.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.site import Site
from backend.app.schemas.site import SiteBase, SiteOut

router = APIRouter(prefix="/sites", tags=["Candidate Sites"])


@router.get("", response_model=Dict[str, Any])
def get_sites_geojson(
    district_id: str = Query("wayanad", description="District identifier"),
    tier: Optional[str] = Query(None, description="Filter by temporary_shelter or permanent_site"),
    db: Session = Depends(get_db),
):
    """
    Returns GeoJSON FeatureCollection of candidate relocation sites with carrying capacity breakdowns.
    """
    query = db.query(Site).filter(Site.district_id == district_id)
    if tier:
        query = query.filter(Site.tier == tier)

    sites = query.order_by(Site.final_capacity.desc()).all()

    features = []
    for s in sites:
        geom_shape = to_shape(s.geometry)
        props = {
            "id": s.id,
            "district_id": s.district_id,
            "name": s.name,
            "tier": s.tier,
            "area_sqm": s.area_sqm,
            "slope_deg": s.slope_deg,
            "dist_road_m": s.dist_road_m,
            "dist_water_m": s.dist_water_m,
            "cap_land": s.cap_land,
            "cap_water": s.cap_water,
            "cap_sanitation": s.cap_sanitation,
            "cap_road": s.cap_road,
            "cap_services": s.cap_services,
            "final_capacity": s.final_capacity,
            "limiting_factor": s.limiting_factor,
            "allocated_population": s.allocated_population,
            "remaining_capacity": s.remaining_capacity,
            "confidence_level": s.confidence_level,
            "screening_reasons_json": s.screening_reasons_json or [],
            "data_origin": s.data_origin,
        }
        features.append({
            "type": "Feature",
            "id": s.id,
            "geometry": mapping(geom_shape),
            "properties": props,
        })

    return {
        "type": "FeatureCollection",
        "total_count": len(features),
        "district_id": district_id,
        "features": features,
    }


@router.get("/{site_id}", response_model=SiteBase)
def get_site_detail(
    site_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns detailed candidate site model with screening reasons and multi-resource capacities.
    """
    s = db.query(Site).filter(Site.id == site_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Site not found")

    return SiteBase(
        id=s.id,
        district_id=s.district_id,
        name=s.name,
        tier=s.tier,
        area_sqm=s.area_sqm,
        slope_deg=s.slope_deg,
        dist_road_m=s.dist_road_m,
        dist_water_m=s.dist_water_m,
        cap_land=s.cap_land,
        cap_water=s.cap_water,
        cap_sanitation=s.cap_sanitation,
        cap_road=s.cap_road,
        cap_services=s.cap_services,
        final_capacity=s.final_capacity,
        limiting_factor=s.limiting_factor,
        allocated_population=s.allocated_population,
        remaining_capacity=s.remaining_capacity,
        confidence_level=s.confidence_level,
        screening_reasons_json=s.screening_reasons_json or [],
        data_origin=s.data_origin,
    )
