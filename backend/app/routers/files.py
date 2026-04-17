"""Lista wszystkich plików danych w katalogu /data."""

import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil

from app.parsers.grib2_parser import list_grib2_files
from app.parsers.netcdf_parser import list_netcdf_files
from app.parsers.hdf5_parser import list_hdf5_files

router = APIRouter()
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))


@router.get("/")
def list_all_files():
    """Zwraca wszystkie obsługiwane pliki pogrupowane według formatu."""
    return {
        "grib2": list_grib2_files(),
        "netcdf": list_netcdf_files(),
        "hdf5": list_hdf5_files(),
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Wgraj plik danych przez HTTP.
    Obsługiwane rozszerzenia: .grib2, .grb2, .nc, .nc4, .h5, .hdf5
    """
    allowed = {".grib2", ".grb2", ".grb", ".grib", ".nc", ".nc4", ".h5", ".hdf5", ".hdf", ".he5"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Nieobsługiwany format: {suffix}")

    dest = DATA_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"message": "Wgrano plik", "filename": file.filename, "size_mb": round(dest.stat().st_size / 1_048_576, 2)}
