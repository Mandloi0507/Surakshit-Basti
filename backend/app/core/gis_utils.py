from typing import Any, Tuple, Union
import geopandas as gpd
from pyproj import CRS


class CRSMismatchError(ValueError):
    """Raised when two spatial datasets do not share the exact same CRS."""
    pass


class MissingCRSError(ValueError):
    """Raised when a spatial dataset is missing a CRS definition."""
    pass


def assert_same_crs(
    a: Union[gpd.GeoDataFrame, gpd.GeoSeries, CRS, str, int],
    b: Union[gpd.GeoDataFrame, gpd.GeoSeries, CRS, str, int],
) -> None:
    """
    Asserts that two spatial datasets/objects have a defined CRS and that they match.
    Raises MissingCRSError if either is missing a CRS.
    Raises CRSMismatchError if CRS does not match.
    """
    def _extract_crs(obj: Any) -> CRS:
        if isinstance(obj, (gpd.GeoDataFrame, gpd.GeoSeries)):
            if obj.crs is None:
                raise MissingCRSError("GeoDataFrame/GeoSeries has no CRS defined (crs is None).")
            return obj.crs
        if isinstance(obj, CRS):
            return obj
        if obj is None:
            raise MissingCRSError("CRS is None.")
        return CRS.from_user_input(obj)

    crs_a = _extract_crs(a)
    crs_b = _extract_crs(b)

    if not crs_a.equals(crs_b):
        raise CRSMismatchError(
            f"CRS mismatch: dataset A has '{crs_a.to_string()}' while dataset B has '{crs_b.to_string()}'."
        )


def get_utm_crs_for_lon_lat(lon: float, lat: float) -> CRS:
    """
    Derives the appropriate EPSG code for the UTM zone of a given (lon, lat) coordinate.
    For India:
    - Northern hemisphere (lat >= 0): EPSG 32600 + zone
    - Zone = int((lon + 180) / 6) + 1
    """
    zone = int((lon + 180) / 6) + 1
    epsg_code = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg_code)


def get_district_utm_crs(bbox: Tuple[float, float, float, float]) -> CRS:
    """
    Computes UTM CRS from a district bounding box (minx, miny, maxx, maxy) in WGS84.
    """
    minx, miny, maxx, maxy = bbox
    centroid_lon = (minx + maxx) / 2.0
    centroid_lat = (miny + maxy) / 2.0
    return get_utm_crs_for_lon_lat(centroid_lon, centroid_lat)
