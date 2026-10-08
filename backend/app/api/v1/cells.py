"""
Cells API router: provides GeoJSON endpoints for terrain hazard grid cells.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.cell import Cell
from backend.app.schemas.cell import CellBase, CellGeoJSONFeature

router = APIRouter(prefix="/cells", tags=["Hazard Grid Cells"])


@router.get("", response_model=Dict[str, Any])
def get_cells(
    district_id: str = Query("wayanad", description="District identifier"),
    hazard_class: Optional[str] = Query(None, description="Filter by Red, Amber, Green"),
    limit: int = Query(2000, ge=1, le=5000, description="Max cells to return"),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns a standard GeoJSON FeatureCollection of terrain cells for the district.
    """
    query = db.query(Cell).filter(Cell.district_id == district_id)
    if hazard_class:
        query = query.filter(Cell.hazard_class == hazard_class)

    total_count = query.count()
    cells = query.offset(offset).limit(limit).all()

    features = []
    for c in cells:
        geom_shape = to_shape(c.geometry)
        props = {
            "id": c.id,
            "district_id": c.district_id,
            "slope_deg": c.slope_deg,
            "aspect_deg": c.aspect_deg,
            "curvature": c.curvature,
            "flow_accum": c.flow_accum,
            "wetness_index": c.wetness_index,
            "hand_m": c.hand_m,
            "dist_drainage_m": c.dist_drainage_m,
            "dist_road_m": c.dist_road_m,
            "lulc_class": c.lulc_class,
            "landslide_score": c.landslide_score,
            "flood_score": c.flood_score,
            "flash_flood_score": c.flash_flood_score,
            "coastal_score": c.coastal_score,
            "structural_hazard": c.structural_hazard,
            "combined_hazard": c.combined_hazard,
            "hazard_class": c.hazard_class,
            "factor_contributions_json": c.factor_contributions_json or {},
            "data_origin": c.data_origin,
        }
        features.append({
            "type": "Feature",
            "id": c.id,
            "geometry": mapping(geom_shape),
            "properties": props,
        })

    return {
        "type": "FeatureCollection",
        "total_count": total_count,
        "returned_count": len(features),
        "district_id": district_id,
        "features": features,
    }
