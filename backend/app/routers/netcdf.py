from fastapi import APIRouter, HTTPException, Query
from app.parsers.netcdf_parser import get_netcdf_info, to_geojson_points

router = APIRouter()


@router.get("/{filename}/info")
def netcdf_info(filename: str):
    try:
        return get_netcdf_info(filename)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd odczytu NetCDF: {e}")


@router.get("/{filename}/geojson")
def netcdf_geojson(
    filename: str,
    variable: str = Query(..., description="Nazwa zmiennej, np. 'sst', 'temp', 'u10'"),
    time_idx: int = Query(0),
    depth_idx: int = Query(0),
    subsample: int = Query(2, ge=1, le=20),
):
    """
    Zwraca GeoJSON z punktami dla wybranej zmiennej NetCDF.
    Automatycznie wykrywa nazwy osi lat/lon (lat/latitude/y/nav_lat itp.).
    """
    try:
        return to_geojson_points(filename, variable, time_idx, depth_idx, subsample)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd konwersji NetCDF: {e}")
