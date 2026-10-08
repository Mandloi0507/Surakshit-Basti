from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.provenance import (
    DataOrigin,
    FreshnessStatus,
    ProvenanceEnvelope,
    create_provenance,
)
from backend.app.core.settings import get_settings
from backend.app.database import test_database_connection


router = APIRouter()


class DataSourceStatus(BaseModel):
    source_name: str
    provenance: ProvenanceEnvelope
    configured: bool
    details: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime
    active_district: Dict[str, Any]
    database: Dict[str, Any]
    data_sources: Dict[str, DataSourceStatus]


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status():
    settings = get_settings()
    now = datetime.now(timezone.utc)

    # 1. District info
    try:
        district: DistrictConfig = load_district_config()
        district_info = {
            "id": district.id,
            "name": district.name,
            "state": district.state,
            "bbox": district.bbox,
            "projected_crs": district.projected_crs,
            "grid_resolution_m": district.grid_resolution_m,
            "hazards_active": district.hazards_active,
        }
    except Exception as e:
        district_info = {
            "id": settings.ACTIVE_DISTRICT,
            "error": f"Failed to load district config: {str(e)}",
        }

    # 2. Database status
    try:
        postgis_ver = test_database_connection()
        db_status = {
            "connected": True,
            "postgis_version": postgis_ver,
        }
    except Exception as e:
        db_status = {
            "connected": False,
            "error": str(e),
        }

    # 3. Data Sources Status & Provenance
    data_sources = {
        "nasa_gpm_imerg": DataSourceStatus(
            source_name="NASA GPM IMERG Early/Late Run NRT",
            provenance=create_provenance(
                source="NASA Earthdata / PPS",
                origin=DataOrigin.LIVE if settings.has_pps_credentials else DataOrigin.UNAVAILABLE,
                license="NASA Open Data",
                notes="Near-Real-Time 30-minute global precipitation",
                now=now,
            ),
            configured=settings.has_pps_credentials,
            details={
                "has_pps_credentials": settings.has_pps_credentials,
                "has_earthdata_token": settings.has_earthdata_token,
                "base_url": settings.NASA_GPM_BASE_URL,
            },
        ),
        "copernicus_dem": DataSourceStatus(
            source_name="Copernicus DEM GLO-30",
            provenance=create_provenance(
                source="Copernicus / AWS S3 Open Data",
                origin=DataOrigin.CACHED,
                license="Copernicus Open Access / CC-BY",
                notes="30m global digital elevation model",
                now=now,
            ),
            configured=True,
            details={"s3_bucket": settings.COPERNICUS_DEM_BUCKET},
        ),
        "esa_worldcover": DataSourceStatus(
            source_name="ESA WorldCover 2021 v200",
            provenance=create_provenance(
                source="ESA / AWS S3 Open Data",
                origin=DataOrigin.CACHED,
                license="CC-BY 4.0",
                notes="10m global land use and land cover",
                now=now,
            ),
            configured=True,
            details={"s3_bucket": settings.ESA_WORLDCOVER_BUCKET},
        ),
        "openstreetmap": DataSourceStatus(
            source_name="OpenStreetMap Hybrid Ladder",
            provenance=create_provenance(
                source="OpenStreetMap",
                origin=DataOrigin.CACHED,
                license="ODbL 1.0",
                notes="Road network and critical facilities",
                now=now,
            ),
            configured=bool(settings.OSM_OVERPASS_URL),
            details={"overpass_endpoint": settings.OSM_OVERPASS_URL},
        ),
    }

    return SystemStatusResponse(
        status="operational",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=now,
        active_district=district_info,
        database=db_status,
        data_sources=data_sources,
    )
