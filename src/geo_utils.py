import geopandas as gpd
from pathlib import Path
from shapely.wkt import loads

from src.exceptions import WKTError


def is_wkt(text: str) -> bool:
    """Check if the input string is in WKT format."""
    try:
        loads(text)
        return True
    except Exception:
        return False

def to_openeo_wkt(aoi: Path | str | None) -> str | None:
    """Returns WKT coordinates of area extent"""
    if aoi is None:
        return None

    if isinstance(aoi, str):
        if is_wkt(aoi):
            return aoi
        else:
            try:
                gdf = gpd.read_file(aoi)
                return gdf.unary_union.wkt
            except Exception as e:
                raise WKTError(e)

    try:
        gdf = gpd.read_file(aoi)
        return gdf.unary_union.wkt
    except Exception as e:
        raise WKTError(e)
