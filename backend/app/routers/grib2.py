from fastapi import APIRouter, HTTPException, Query
from app.parsers.grib2_parser import get_grib2_info, to_geojson_points

router = APIRouter()


@router.get("/{filename}/info")
def grib2_info(filename: str):
    """Metadane pliku GRIB2: zmienne, wymiary, zakres przestrzenny."""
    try:
        return get_grib2_info(filename)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd odczytu GRIB2: {e}")


@router.get("/{filename}/geojson")
def grib2_geojson(
    filename: str,
    variable: str = Query(..., description="Nazwa zmiennej, np. 't2m'"),
    time_idx: int = Query(0, description="Indeks czasu (0 = pierwszy krok)"),
    level_idx: int = Query(0, description="Indeks poziomu (0 = powierzchnia)"),
    subsample: int = Query(4, ge=1, le=20, description="Co N-ty punkt (1=wszystkie)"),
):
    """
    Zwraca GeoJSON z punktami dla wybranej zmiennej GRIB2.
    Użyj /info żeby sprawdzić dostępne zmienne.
    """
    try:
        return to_geojson_points(filename, variable, time_idx, level_idx, subsample)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Błąd konwersji GRIB2: {e}")
