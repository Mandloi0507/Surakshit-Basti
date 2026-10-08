import pytest
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS

from backend.app.core.gis_utils import (
    CRSMismatchError,
    MissingCRSError,
    assert_same_crs,
    get_utm_crs_for_lon_lat,
    get_district_utm_crs,
)


def test_assert_same_crs_matching():
    gdf1 = gpd.GeoDataFrame({"geometry": [Point(76.0, 11.5)]}, crs="EPSG:4326")
    gdf2 = gpd.GeoDataFrame({"geometry": [Point(76.1, 11.6)]}, crs="EPSG:4326")

    # Should not raise
    assert_same_crs(gdf1, gdf2)
    assert_same_crs("EPSG:4326", "EPSG:4326")


def test_assert_same_crs_mismatch():
    gdf1 = gpd.GeoDataFrame({"geometry": [Point(76.0, 11.5)]}, crs="EPSG:4326")
    gdf2 = gpd.GeoDataFrame({"geometry": [Point(76.1, 11.6)]}, crs="EPSG:32643")

    with pytest.raises(CRSMismatchError):
        assert_same_crs(gdf1, gdf2)


def test_assert_same_crs_missing():
    gdf_none = gpd.GeoDataFrame({"geometry": [Point(76.0, 11.5)]})  # crs=None
    gdf_valid = gpd.GeoDataFrame({"geometry": [Point(76.1, 11.6)]}, crs="EPSG:4326")

    with pytest.raises(MissingCRSError):
        assert_same_crs(gdf_none, gdf_valid)


def test_utm_crs_derivation():
    # Lon 76.13, Lat 11.53 (Wayanad, Kerala) -> Zone 43N (EPSG:32643)
    utm_crs = get_utm_crs_for_lon_lat(76.13, 11.53)
    assert utm_crs == CRS.from_epsg(32643)

    bbox_wayanad = (75.78, 11.45, 76.45, 12.00)
    district_crs = get_district_utm_crs(bbox_wayanad)
    assert district_crs == CRS.from_epsg(32643)
