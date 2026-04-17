from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.parsers.hdf5_parser import get_hdf5_info, hdf5_dataset_to_geojson

router = APIRouter()


@router.get("/{filename:path}/info")
def hdf5_info(filename: str):
    """
    Struktura pliku HDF5. Dla ODIM HDF5 zwraca dodatkowo:
    - odim: true
    - projdef, xsize, ysize, xscale, yscale, xllcorner, yllcorner
    - datasets: lista grup datasetN z polami data_fields
    """
    try:
        return get_hdf5_info(filename)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd odczytu HDF5: {e}")


@router.get("/{filename:path}/geojson")
def hdf5_geojson(
    filename: str,
    dataset_path: str = Query(..., description="Ścieżka do datasetu, np. /dataset1/data1/data"),
    lat_path: Optional[str] = Query(None),
    lon_path: Optional[str] = Query(None),
    time_idx: int = Query(0),
    subsample: int = Query(4, ge=1, le=20),
    scale_factor: Optional[float] = Query(None),
    fill_value: Optional[float] = Query(None),
):
    """
    Konwertuje dataset HDF5 → GeoJSON punktów.
    Dla ODIM HDF5 automatycznie przelicza projekcję kartograficzną → lat/lon.
    """
    try:
        return hdf5_dataset_to_geojson(
            filename, dataset_path, lat_path, lon_path,
            time_idx, subsample, scale_factor, fill_value,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd konwersji HDF5: {e}")
