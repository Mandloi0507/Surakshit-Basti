import math
from typing import Any, Dict, List, Optional
from shapely.geometry import box
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.database import SessionLocal
from backend.app.engines.hazard_engine import CellFactors, compute_cell_hazard
from backend.app.models.district import District
from backend.app.models.cell import Cell

logger = get_logger(__name__)


def ensure_district_in_db(district_id: str, session: Session) -> District:
    """Ensures the district record exists in the database, inserting from config if needed."""
    district_obj = session.query(District).filter(District.id == district_id).first()
    if not district_obj:
        config: DistrictConfig = load_district_config(district_id)
        district_obj = District(
            id=config.id,
            name=config.name,
            state=config.state,
            bbox_json=list(config.bbox),
            projected_crs=config.projected_crs,
            grid_resolution_m=config.grid_resolution_m,
        )
        session.add(district_obj)
        session.flush()
    return district_obj


def generate_district_cell_grid(
    district_id: str,
    grid_size_deg: float = 0.01,  # ~1km resolution for pilot cell vector representation
) -> List[Dict[str, Any]]:
    """
    Generates a regular grid of vector cells covering the district bounding box.
    """
    district: DistrictConfig = load_district_config(district_id)
    minx, miny, maxx, maxy = district.bbox

    cols = math.ceil((maxx - minx) / grid_size_deg)
    rows = math.ceil((maxy - miny) / grid_size_deg)

    cells = []
    idx = 1
    for r in range(rows):
        for c in range(cols):
            c_minx = minx + c * grid_size_deg
            c_maxx = min(maxx, c_minx + grid_size_deg)
            c_miny = miny + r * grid_size_deg
            c_maxy = min(maxy, c_miny + grid_size_deg)

            poly = box(c_minx, c_miny, c_maxx, c_maxy)
            center_lon = (c_minx + c_maxx) / 2.0
            center_lat = (c_miny + c_maxy) / 2.0

            # Deterministic terrain factor variation across coordinates for pilot demonstration
            pseudo_elevation = 700.0 + 800.0 * math.sin(center_lat * 20.0) * math.cos(center_lon * 20.0)
            pseudo_slope = max(2.0, min(55.0, abs(pseudo_elevation - 700.0) / 25.0 + 10.0 * math.sin(center_lon * 50.0)))
            pseudo_hand = max(0.5, 30.0 * (1.0 - math.exp(-pseudo_slope / 15.0)))
            pseudo_dist_drainage = max(10.0, 500.0 * abs(math.sin(center_lat * 30.0)))
            pseudo_dist_road = max(15.0, 800.0 * abs(math.cos(center_lon * 30.0)))

            factors = CellFactors(
                slope_deg=round(float(pseudo_slope), 2),
                aspect_deg=round(float(180.0 + 90.0 * math.sin(center_lat * 10.0)), 1),
                curvature=round(float(0.05 * math.cos(center_lon * 10.0)), 3),
                flow_accum=round(float(max(1.0, 1000.0 / (pseudo_slope + 0.1))), 1),
                wetness_index=round(float(max(3.0, 15.0 - pseudo_hand / 3.0)), 2),
                hand_m=round(float(pseudo_hand), 2),
                dist_drainage_m=round(float(pseudo_dist_drainage), 1),
                dist_road_m=round(float(pseudo_dist_road), 1),
                lulc_class="Tree cover" if pseudo_slope > 25.0 else ("Cropland" if pseudo_slope > 10.0 else "Built-up"),
                past_event_count=1 if (center_lat > 11.50 and center_lat < 11.58 and center_lon > 76.10 and center_lon < 76.18) else 0,
            )

            hazard = compute_cell_hazard(
                factors,
                landslide_weights=district.weights.landslide,
                flood_weights=district.weights.flood,
                threshold_red=district.thresholds.red_zone_min,
                threshold_amber=district.thresholds.amber_zone_min,
            )

            cell_id = f"{district_id}_cell_{idx:05d}"
            cells.append({
                "id": cell_id,
                "district_id": district_id,
                "geometry": poly,
                "slope_deg": float(factors.slope_deg),
                "aspect_deg": float(factors.aspect_deg),
                "curvature": float(factors.curvature),
                "flow_accum": float(factors.flow_accum),
                "wetness_index": float(factors.wetness_index),
                "hand_m": float(factors.hand_m),
                "dist_drainage_m": float(factors.dist_drainage_m),
                "dist_road_m": float(factors.dist_road_m),
                "lulc_class": str(factors.lulc_class),
                "landslide_score": float(hazard.landslide_score),
                "flood_score": float(hazard.flood_score),
                "flash_flood_score": float(hazard.flash_flood_score),
                "coastal_score": float(hazard.coastal_score),
                "structural_hazard": float(hazard.structural_hazard),
                "combined_hazard": float(hazard.combined_hazard),
                "hazard_class": str(hazard.hazard_class),
                "factor_contributions_json": hazard.factor_contributions,
                "data_origin": DataOrigin.DEMO_SYNTHETIC.value,
            })
            idx += 1

    return cells


def populate_district_cells_in_db(district_id: str, db: Optional[Session] = None) -> int:
    """
    Populates or updates the cells table in PostGIS for the given district.
    """
    session = db or SessionLocal()
    should_close = db is None

    try:
        # 1. Ensure district exists
        ensure_district_in_db(district_id, session)

        # 2. Generate cells
        grid_data = generate_district_cell_grid(district_id)
        logger.info(f"Generating {len(grid_data)} terrain cells for district={district_id}")

        # 3. Delete existing cells for district
        session.query(Cell).filter(Cell.district_id == district_id).delete()
        session.flush()

        # 4. Insert new cells
        for item in grid_data:
            geom_wkt = item["geometry"].wkt
            cell = Cell(
                id=item["id"],
                district_id=item["district_id"],
                geometry=WKTElement(geom_wkt, srid=4326),
                slope_deg=item["slope_deg"],
                aspect_deg=item["aspect_deg"],
                curvature=item["curvature"],
                flow_accum=item["flow_accum"],
                wetness_index=item["wetness_index"],
                hand_m=item["hand_m"],
                dist_drainage_m=item["dist_drainage_m"],
                dist_road_m=item["dist_road_m"],
                lulc_class=item["lulc_class"],
                landslide_score=item["landslide_score"],
                flood_score=item["flood_score"],
                flash_flood_score=item["flash_flood_score"],
                coastal_score=item["coastal_score"],
                structural_hazard=item["structural_hazard"],
                combined_hazard=item["combined_hazard"],
                hazard_class=item["hazard_class"],
                factor_contributions_json=item["factor_contributions_json"],
                data_origin=item["data_origin"],
            )
            session.add(cell)

        session.commit()
        logger.info(f"Successfully populated {len(grid_data)} cells into PostGIS database.")
        return len(grid_data)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to populate cells in database: {e}")
        raise
    finally:
        if should_close:
            session.close()
