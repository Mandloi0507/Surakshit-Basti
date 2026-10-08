import argparse
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
import requests
import botocore
import botocore.client
import boto3

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.core.settings import get_settings
from backend.app.ingestion.manifest import DatasetManifest, compute_sha256, save_manifest

logger = get_logger(__name__)


def get_dem_tile_names_for_bbox(bbox: Tuple[float, float, float, float]) -> List[str]:
    """
    Computes Copernicus DEM GLO-30 1-degree tile names intersecting the bbox (minx, miny, maxx, maxy).
    """
    minx, miny, maxx, maxy = bbox
    min_lat = math.floor(miny)
    max_lat = math.floor(maxy)
    min_lon = math.floor(minx)
    max_lon = math.floor(maxx)

    tiles = []
    for lat in range(min_lat, max_lat + 1):
        for lon in range(min_lon, max_lon + 1):
            ns = "N" if lat >= 0 else "S"
            ew = "E" if lon >= 0 else "W"
            tile_name = f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
            tiles.append(tile_name)
    return tiles


def download_copernicus_dem(
    district_id: str,
    output_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> DatasetManifest:
    """
    Downloads Copernicus DEM GLO-30 tiles for a district from public AWS S3 unsigned bucket.
    """
    settings = get_settings()
    district: DistrictConfig = load_district_config(district_id)
    tiles = get_dem_tile_names_for_bbox(district.bbox)

    target_dir = output_dir or (settings.DATA_PATH / "raw" / "copernicus_dem" / district_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    bucket_name = settings.COPERNICUS_DEM_BUCKET
    s3_client = boto3.client("s3", config=botocore.client.Config(signature_version=botocore.UNSIGNED))

    downloaded_files = []
    checksums = {}

    logger.info(f"Copernicus DEM ingestion for district={district_id} (tiles: {tiles})")

    for tile in tiles:
        key = f"{tile}/{tile}.tif"
        local_file = target_dir / f"{tile}.tif"

        if dry_run:
            logger.info(f"[DRY-RUN] Would download s3://{bucket_name}/{key} -> {local_file}")
            # If dry-run and file doesn't exist, create a lightweight synthetic/mock placeholder if needed
            downloaded_files.append(str(local_file.relative_to(settings.PROJECT_ROOT_PATH)))
            checksums[str(local_file.relative_to(settings.PROJECT_ROOT_PATH))] = "dry_run_placeholder"
            continue

        if local_file.exists() and local_file.stat().st_size > 1000:
            logger.info(f"Tile already exists in cache: {local_file}")
        else:
            try:
                logger.info(f"Downloading s3://{bucket_name}/{key} -> {local_file}")
                s3_client.download_file(bucket_name, key, str(local_file))
            except Exception as e:
                logger.warning(f"S3 download failed ({e}), attempting HTTPS fallback...")
                url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
                resp = requests.get(url, stream=True, timeout=30)
                resp.raise_for_status()
                with open(local_file, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)

        rel_path = str(local_file.relative_to(settings.PROJECT_ROOT_PATH))
        downloaded_files.append(rel_path)
        checksums[rel_path] = compute_sha256(local_file)

    manifest = DatasetManifest(
        dataset_id="copernicus_dem_glo30",
        district_id=district_id,
        source="Copernicus / AWS S3 Open Data",
        dataset_name="Copernicus DEM GLO-30",
        version="2021",
        license="Copernicus Open Access / CC-BY",
        access_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        bbox=list(district.bbox),
        crs="EPSG:4326",
        resolution="30m",
        file_paths=downloaded_files,
        checksums=checksums,
        processing_status="raw_downloaded",
        script="backend.app.ingestion.copernicus_dem",
        data_origin=DataOrigin.CACHED,
    )

    save_manifest(manifest)
    logger.info(f"Saved manifest for {manifest.dataset_id} in district {district_id}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Copernicus DEM GLO-30 tiles for a district")
    parser.add_argument("--district", type=str, default="wayanad", help="District ID")
    parser.add_argument("--dry-run", action="store_true", help="Check reachability and tiles without downloading")
    args = parser.parse_args()

    download_copernicus_dem(args.district, dry_run=args.dry_run)
