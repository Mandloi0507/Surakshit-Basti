from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.app.core.provenance import DataOrigin
from backend.app.ingestion.copernicus_dem import get_dem_tile_names_for_bbox, download_copernicus_dem
from backend.app.ingestion.worldcover import get_worldcover_tile_names_for_bbox, download_worldcover
from backend.app.ingestion.imerg import fetch_imerg_rainfall
from backend.app.ingestion.osm import (
    build_overpass_query_for_bbox,
    parse_overpass_elements_to_gdf,
    ingest_osm_hybrid,
)
from backend.app.ingestion.manifest import DatasetManifest, compute_sha256, save_manifest


def test_copernicus_dem_tile_names():
    # Wayanad bbox: [75.78, 11.45, 76.45, 12.00]
    bbox = (75.78, 11.45, 76.45, 12.00)
    tiles = get_dem_tile_names_for_bbox(bbox)
    assert len(tiles) >= 2
    assert "Copernicus_DSM_COG_10_N11_00_E075_00_DEM" in tiles
    assert "Copernicus_DSM_COG_10_N11_00_E076_00_DEM" in tiles


def test_worldcover_tile_names():
    # Wayanad bbox falls in 3x3 degree tile N09E075 (lat 9-12, lon 75-78)
    bbox = (75.78, 11.45, 76.45, 12.00)
    tiles = get_worldcover_tile_names_for_bbox(bbox)
    assert "ESA_WorldCover_10m_2021_v200_N09E075_Map" in tiles


def test_overpass_query_builder():
    bbox = (75.78, 11.45, 76.45, 12.00)
    query = build_overpass_query_for_bbox(bbox)
    assert "11.45,75.78,12.0,76.45" in query
    assert "highway" in query
    assert "waterway" in query


def test_overpass_elements_parser():
    mock_elements = [
        {
            "id": 1001,
            "tags": {"highway": "primary", "name": "Main Highway"},
            "geometry": [{"lat": 11.5, "lon": 76.0}, {"lat": 11.6, "lon": 76.1}],
        },
        {
            "id": 2001,
            "tags": {"waterway": "river", "name": "Kabini River"},
            "geometry": [{"lat": 11.52, "lon": 76.02}, {"lat": 11.54, "lon": 76.05}],
        },
        {
            "id": 3001,
            "tags": {"amenity": "hospital", "name": "Community Health Centre"},
            "lat": 11.55,
            "lon": 76.08,
        },
    ]

    gdfs = parse_overpass_elements_to_gdf(mock_elements)
    assert len(gdfs["roads"]) == 1
    assert gdfs["roads"].iloc[0]["name"] == "Main Highway"
    assert len(gdfs["waterways"]) == 1
    assert gdfs["waterways"].iloc[0]["name"] == "Kabini River"
    assert len(gdfs["health_facilities"]) == 1
    assert gdfs["health_facilities"].iloc[0]["name"] == "Community Health Centre"


def test_imerg_dry_run():
    data, manifest = fetch_imerg_rainfall("wayanad", dry_run=True)
    assert data["district_id"] == "wayanad"
    assert "mean_rainfall_24h_mm" in data
    assert manifest.dataset_id == "nasa_gpm_imerg_nrt"
    assert manifest.data_origin in (DataOrigin.CACHED, DataOrigin.LIVE)


def test_copernicus_dem_dry_run():
    manifest = download_copernicus_dem("wayanad", dry_run=True)
    assert manifest.dataset_id == "copernicus_dem_glo30"
    assert manifest.resolution == "30m"
    assert len(manifest.file_paths) >= 1


def test_worldcover_dry_run():
    manifest = download_worldcover("wayanad", dry_run=True)
    assert manifest.dataset_id == "esa_worldcover_2021"
    assert manifest.resolution == "10m"
    assert len(manifest.file_paths) >= 1


def test_osm_ladder_fallback_when_network_fails(tmp_path: Path):
    # Mock requests.post to fail
    with patch("requests.post", side_effect=Exception("Overpass 504 Gateway Timeout")):
        gdfs, manifest = ingest_osm_hybrid("wayanad", output_dir=tmp_path)
        # Should gracefully fall down the ladder without crashing
        assert "roads" in gdfs
        assert manifest.dataset_id == "osm_hybrid_network"
        assert manifest.data_origin in (DataOrigin.CACHED, DataOrigin.UNAVAILABLE)
