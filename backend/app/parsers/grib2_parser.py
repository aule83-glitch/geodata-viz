"""
Parser GRIB2 — odczyt przez cfgrib + xarray.

GRIB2 to binarny format ECMWF używany przez modele pogodowe (ERA5, GFS, ICON, AROME).
Dane są na siatce regularnej lub zredukowanej gaussowskiej.

Przykładowe użycie:
    ds = open_grib2("era5_t2m.grib2")
    geojson = to_geojson_points(ds, variable="t2m", level=0)
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Optional

import xarray as xr


DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))


def list_grib2_files() -> list[dict]:
    """Zwraca listę plików .grib2 / .grb2 / .grb w katalogu danych."""
    exts = {".grib2", ".grb2", ".grb", ".grib"}
    files = []
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() in exts:
            files.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / 1_048_576, 2),
                "path": str(f),
            })
    return files


def open_grib2(filename: str) -> xr.Dataset:
    """
    Otwiera plik GRIB2 jako xarray.Dataset.
    cfgrib automatycznie odczytuje metadane (parametr, poziom, czas).
    Pliki wielopolowe (np. ERA5 z wieloma zmiennymi) mogą wymagać backend_kwargs.
    """
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    # squeeze=False zachowuje wszystkie wymiary (time, level, lat, lon)
    ds = xr.open_dataset(
        str(path),
        engine="cfgrib",
        backend_kwargs={"indexing_time": "wall_clock"},
    )
    return ds


def get_grib2_info(filename: str) -> dict:
    """Zwraca metadane: zmienne, wymiary, zakres współrzędnych, czasy."""
    ds = open_grib2(filename)
    info = {
        "filename": filename,
        "variables": {},
        "dims": dict(ds.dims),
        "coords": {},
    }
    for name, var in ds.data_vars.items():
        attrs = var.attrs
        info["variables"][name] = {
            "long_name": attrs.get("long_name", name),
            "units": attrs.get("units", "?"),
            "dims": list(var.dims),
            "shape": list(var.shape),
            "min": float(np.nanmin(var.values)),
            "max": float(np.nanmax(var.values)),
        }
    if "latitude" in ds.coords:
        lats = ds.coords["latitude"].values
        lons = ds.coords["longitude"].values
        info["coords"]["lat_range"] = [float(lats.min()), float(lats.max())]
        info["coords"]["lon_range"] = [float(lons.min()), float(lons.max())]
    return info


def to_geojson_points(
    filename: str,
    variable: str,
    time_idx: int = 0,
    level_idx: int = 0,
    subsample: int = 4,       # co N-ty punkt, żeby nie przeciążyć frontendu
) -> dict:
    """
    Konwertuje pole GRIB2 (2D siatkę lat/lon) na GeoJSON FeatureCollection punktów.
    Każdy punkt ma atrybut 'value' z wartością zmiennej.

    subsample=4 → co 4. punkt w obu kierunkach (16x mniej punktów)
    subsample=1 → wszystkie punkty (może być wolno dla ERA5 0.25°)
    """
    ds = open_grib2(filename)

    if variable not in ds.data_vars:
        raise ValueError(f"Zmienna '{variable}' nie istnieje. Dostępne: {list(ds.data_vars)}")

    var = ds[variable]

    # Wybierz przekrój przez czas i poziom (jeśli istnieją)
    if "time" in var.dims:
        var = var.isel(time=time_idx)
    if "step" in var.dims:
        var = var.isel(step=0)
    if "isobaricInhPa" in var.dims or "level" in var.dims:
        dim = "isobaricInhPa" if "isobaricInhPa" in var.dims else "level"
        var = var.isel(**{dim: level_idx})

    data = var.values          # shape: (lat, lon)
    lats = ds.coords["latitude"].values
    lons = ds.coords["longitude"].values

    # Subsampling
    lats_s = lats[::subsample]
    lons_s = lons[::subsample]
    data_s = data[::subsample, ::subsample]

    features = []
    for i, lat in enumerate(lats_s):
        for j, lon in enumerate(lons_s):
            val = data_s[i, j]
            if np.isnan(val):
                continue
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": {
                    "value": round(float(val), 4),
                    "variable": variable,
                    "units": ds[variable].attrs.get("units", ""),
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "variable": variable,
            "units": ds[variable].attrs.get("units", ""),
            "long_name": ds[variable].attrs.get("long_name", variable),
            "count": len(features),
            "vmin": float(np.nanmin(data)),
            "vmax": float(np.nanmax(data)),
        },
    }
