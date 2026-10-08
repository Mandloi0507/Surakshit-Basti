import argparse
from datetime import datetime, timezone
from typing import Any, Dict
from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.ingestion.copernicus_dem import download_copernicus_dem
from backend.app.ingestion.worldcover import download_worldcover
from backend.app.ingestion.imerg import fetch_imerg_rainfall
from backend.app.ingestion.osm import ingest_osm_hybrid

logger = get_logger(__name__)


def run_district_ingestion_pipeline(district_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Orchestrates ingestion of all required open data feeds for a district:
    1. Copernicus DEM GLO-30 (elevation & terrain)
    2. ESA WorldCover 2021 v200 (land cover)
    3. NASA GPM IMERG NRT (rainfall observations)
    4. OpenStreetMap (roads, waterways, health facilities)
    """
    district: DistrictConfig = load_district_config(district_id)
    logger.info(f"Starting ingestion pipeline for district={district.name} ({district_id})")

    results = {}

    # 1. Copernicus DEM
    logger.info("--> [1/4] Ingesting Copernicus DEM...")
    dem_manifest = download_copernicus_dem(district_id, dry_run=dry_run)
    results["copernicus_dem"] = dem_manifest.model_dump()

    # 2. ESA WorldCover
    logger.info("--> [2/4] Ingesting ESA WorldCover...")
    wc_manifest = download_worldcover(district_id, dry_run=dry_run)
    results["esa_worldcover"] = wc_manifest.model_dump()

    # 3. NASA GPM IMERG
    logger.info("--> [3/4] Ingesting NASA GPM IMERG Rainfall...")
    _, imerg_manifest = fetch_imerg_rainfall(district_id, dry_run=dry_run)
    results["nasa_gpm_imerg"] = imerg_manifest.model_dump()

    # 4. OpenStreetMap
    logger.info("--> [4/4] Ingesting OpenStreetMap Hybrid Ladder...")
    _, osm_manifest = ingest_osm_hybrid(district_id, dry_run=dry_run)
    results["openstreetmap"] = osm_manifest.model_dump()

    logger.info(f"Ingestion pipeline completed for district={district_id} with 4 manifests generated.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete data ingestion pipeline for a district")
    parser.add_argument("--district", type=str, default="wayanad", help="District ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run reachability check without heavy downloads")
    args = parser.parse_args()

    run_district_ingestion_pipeline(args.district, dry_run=args.dry_run)
