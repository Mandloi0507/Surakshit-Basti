import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
import geopandas as gpd
from shapely.geometry import LineString, Point, shape

from backend.app.core.district_config import DistrictConfig, load_district_config
from backend.app.core.logging import get_logger
from backend.app.core.provenance import DataOrigin
from backend.app.core.settings import get_settings
from backend.app.ingestion.manifest import DatasetManifest, compute_sha256, save_manifest

logger = get_logger(__name__)


def build_overpass_query_for_bbox(bbox: Tuple[float, float, float, float]) -> str:
    """Builds Overpass QL query for road networks, waterways, and health amenities."""
    minx, miny, maxx, maxy = bbox
    # Overpass bbox order: (south, west, north, east) -> (miny, minx, maxy, maxx)
    bbox_str = f"{miny},{minx},{maxy},{maxx}"

    query = f"""
    [out:json][timeout:25];
    (
      way["highway"~"primary|secondary|tertiary|residential|unclassified|trunk"]({bbox_str});
      way["waterway"~"river|stream|canal"]({bbox_str});
      node["amenity"~"hospital|clinic|doctors"]({bbox_str});
    );
    out body geom;
    """
    return query.strip()


def parse_overpass_elements_to_gdf(elements: List[Dict[str, Any]]) -> Dict[str, gpd.GeoDataFrame]:
    """Parses Overpass JSON elements into GeoDataFrames for roads, waterways, and health facilities."""
    roads = []
    waterways = []
    amenities = []

    for elem in elements:
        tags = elem.get("tags", {})
        if "highway" in tags and "geometry" in elem:
            coords = [(pt["lon"], pt["lat"]) for pt in elem["geometry"]]
            if len(coords) >= 2:
                roads.append({
                    "osm_id": str(elem.get("id")),
                    "name": tags.get("name", "Unnamed Road"),
                    "highway": tags.get("highway"),
                    "surface": tags.get("surface", "unknown"),
                    "geometry": LineString(coords),
                })
        elif "waterway" in tags and "geometry" in elem:
            coords = [(pt["lon"], pt["lat"]) for pt in elem["geometry"]]
            if len(coords) >= 2:
                waterways.append({
                    "osm_id": str(elem.get("id")),
                    "name": tags.get("name", "Unnamed Waterway"),
                    "waterway": tags.get("waterway"),
                    "geometry": LineString(coords),
                })
        elif "amenity" in tags:
            if "lat" in elem and "lon" in elem:
                amenities.append({
                    "osm_id": str(elem.get("id")),
                    "name": tags.get("name", "Health Facility"),
                    "amenity": tags.get("amenity"),
                    "geometry": Point(elem["lon"], elem["lat"]),
                })

    crs = "EPSG:4326"
    roads_gdf = gpd.GeoDataFrame(roads, crs=crs) if roads else gpd.GeoDataFrame(columns=["osm_id", "name", "highway", "geometry"], crs=crs)
    waterways_gdf = gpd.GeoDataFrame(waterways, crs=crs) if waterways else gpd.GeoDataFrame(columns=["osm_id", "name", "waterway", "geometry"], crs=crs)
    amenities_gdf = gpd.GeoDataFrame(amenities, crs=crs) if amenities else gpd.GeoDataFrame(columns=["osm_id", "name", "amenity", "geometry"], crs=crs)

    return {
        "roads": roads_gdf,
        "waterways": waterways_gdf,
        "health_facilities": amenities_gdf,
    }


def ingest_osm_hybrid(
    district_id: str,
    output_dir: Optional[Path] = None,
    force_live: bool = False,
    dry_run: bool = False,
) -> Tuple[Dict[str, gpd.GeoDataFrame], DatasetManifest]:
    """
    Executes the OSM hybrid ingestion ladder:
    1. LIVE Overpass API (polite, timeout 10s)
    2. CACHED (data/cache/osm/latest_<district>.geojson)
    3. CACHED_EXTRACT (data/raw/osm/ or data/external/osm/)
    4. UNAVAILABLE fallback
    """
    settings = get_settings()
    district: DistrictConfig = load_district_config(district_id)
    now = datetime.now(timezone.utc)

    cache_dir = settings.DATA_PATH / "cache" / "osm"
    raw_dir = settings.DATA_PATH / "raw" / "osm" / district_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    cache_roads = cache_dir / f"{district_id}_roads.geojson"
    cache_water = cache_dir / f"{district_id}_waterways.geojson"
    cache_health = cache_dir / f"{district_id}_health.geojson"

    data_origin = DataOrigin.LIVE
    gdfs = {}

    if dry_run:
        logger.info(f"[DRY-RUN] Checking OSM Overpass query for bbox {district.bbox}")
        # In dry run mode, check if cache exists or return synthetic demo frame
        if cache_roads.exists():
            roads_gdf = gpd.read_file(cache_roads)
            water_gdf = gpd.read_file(cache_water) if cache_water.exists() else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
            health_gdf = gpd.read_file(cache_health) if cache_health.exists() else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
            gdfs = {"roads": roads_gdf, "waterways": water_gdf, "health_facilities": health_gdf}
            data_origin = DataOrigin.CACHED
        else:
            gdfs = parse_overpass_elements_to_gdf([])
            data_origin = DataOrigin.UNAVAILABLE

        manifest = DatasetManifest(
            dataset_id="osm_hybrid_network",
            district_id=district_id,
            source="OpenStreetMap",
            dataset_name="OSM Roads, Waterways & Health",
            license="ODbL 1.0",
            access_date=now.strftime("%Y-%m-%d"),
            bbox=list(district.bbox),
            crs="EPSG:4326",
            resolution="Vector",
            file_paths=[],
            checksums={},
            processing_status="dry_run",
            script="backend.app.ingestion.osm",
            data_origin=data_origin,
        )
        save_manifest(manifest)
        return gdfs, manifest

    # Step 1: Try LIVE Overpass
    live_success = False
    if force_live or not cache_roads.exists():
        query = build_overpass_query_for_bbox(district.bbox)
        logger.info(f"Attempting live Overpass fetch at: {settings.OSM_OVERPASS_URL}")
        try:
            resp = requests.post(settings.OSM_OVERPASS_URL, data={"data": query}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                gdfs = parse_overpass_elements_to_gdf(elements)
                if len(gdfs["roads"]) > 0:
                    gdfs["roads"].to_file(cache_roads, driver="GeoJSON")
                    gdfs["waterways"].to_file(cache_water, driver="GeoJSON")
                    gdfs["health_facilities"].to_file(cache_health, driver="GeoJSON")
                    live_success = True
                    data_origin = DataOrigin.LIVE
                    logger.info(f"Successfully fetched LIVE OSM data: {len(gdfs['roads'])} road segments.")
        except Exception as e:
            logger.warning(f"Live Overpass fetch failed: {e}. Falling down ladder to CACHE...")

    # Step 2: Fall back to CACHED
    if not live_success:
        if cache_roads.exists():
            logger.info(f"Loading CACHED OSM data from {cache_roads}")
            roads_gdf = gpd.read_file(cache_roads)
            water_gdf = gpd.read_file(cache_water) if cache_water.exists() else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
            health_gdf = gpd.read_file(cache_health) if cache_health.exists() else gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")
            gdfs = {"roads": roads_gdf, "waterways": water_gdf, "health_facilities": health_gdf}
            data_origin = DataOrigin.CACHED
        else:
            # Step 3 & 4: Check for regional extract or fallback to UNAVAILABLE
            extract_pbf = settings.DATA_PATH / "external" / "osm" / f"{district_id}.osm.pbf"
            if extract_pbf.exists():
                logger.info(f"Reading regional extract from {extract_pbf}")
                # Read via pyogrio/GDAL OSM driver
                roads_gdf = gpd.read_file(extract_pbf, layer="lines", engine="pyogrio")
                gdfs = {"roads": roads_gdf, "waterways": gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326"), "health_facilities": gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")}
                data_origin = DataOrigin.CACHED
            else:
                logger.warning("No OSM live, cache, or extract available. Setting status to UNAVAILABLE.")
                gdfs = parse_overpass_elements_to_gdf([])
                data_origin = DataOrigin.UNAVAILABLE

    file_paths = []
    checksums = {}
    for path in [cache_roads, cache_water, cache_health]:
        if path.exists():
            rel_p = str(path.relative_to(settings.PROJECT_ROOT_PATH))
            file_paths.append(rel_p)
            checksums[rel_p] = compute_sha256(path)

    manifest = DatasetManifest(
        dataset_id="osm_hybrid_network",
        district_id=district_id,
        source="OpenStreetMap",
        dataset_name="OSM Roads, Waterways & Health",
        license="ODbL 1.0",
        access_date=now.strftime("%Y-%m-%d"),
        bbox=list(district.bbox),
        crs="EPSG:4326",
        resolution="Vector",
        file_paths=file_paths,
        checksums=checksums,
        processing_status="cached_valid" if data_origin == DataOrigin.CACHED else ("live_valid" if data_origin == DataOrigin.LIVE else "unavailable"),
        script="backend.app.ingestion.osm",
        data_origin=data_origin,
    )
    save_manifest(manifest)
    return gdfs, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest OpenStreetMap data using the hybrid ladder")
    parser.add_argument("--district", type=str, default="wayanad", help="District ID")
    parser.add_argument("--force-live", action="store_true", help="Force live Overpass query")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without downloading")
    args = parser.parse_args()

    ingest_osm_hybrid(args.district, force_live=args.force_live, dry_run=args.dry_run)
