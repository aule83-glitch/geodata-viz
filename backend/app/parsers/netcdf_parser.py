"""
Parser NetCDF3/NetCDF4 — xarray z pełną obsługą metadanych.
Naprawiono: long_name w GeoJSON metadata, obsługa różnych nazw osi.
"""
import os, math
import numpy as np
from pathlib import Path
from typing import Optional
import xarray as xr

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))

LAT_NAMES = ["lat", "latitude", "Latitude", "LAT", "LATITUDE", "y", "nav_lat", "rlat"]
LON_NAMES = ["lon", "longitude", "Longitude", "LON", "LONGITUDE", "x", "nav_lon", "rlon"]


def list_netcdf_files() -> list[dict]:
    exts = {".nc", ".nc4", ".netcdf", ".cdf"}
    files = []
    for f in DATA_DIR.rglob("*"):
        if f.suffix.lower() in exts:
            files.append({
                "name": str(f.relative_to(DATA_DIR)),
                "size_mb": round(f.stat().st_size / 1_048_576, 2),
                "path": str(f),
            })
    return files


def open_netcdf(filename: str) -> xr.Dataset:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {filename}")
    try:
        return xr.open_dataset(str(path), decode_times=True)
    except Exception:
        return xr.open_dataset(str(path), decode_times=False)


def get_netcdf_info(filename: str) -> dict:
    ds = open_netcdf(filename)
    variables = {}
    for name, var in ds.data_vars.items():
        try:
            vals = var.values
            vmin = float(np.nanmin(vals)) if np.any(~np.isnan(vals.astype(float))) else 0.0
            vmax = float(np.nanmax(vals)) if np.any(~np.isnan(vals.astype(float))) else 0.0
        except Exception:
            vmin = vmax = 0.0
        variables[name] = {
            "long_name": var.attrs.get("long_name", name),
            "standard_name": var.attrs.get("standard_name", ""),
            "units": var.attrs.get("units", ""),
            "dims": list(var.dims),
            "shape": list(var.shape),
            "min": vmin if not math.isnan(vmin) else 0.0,
            "max": vmax if not math.isnan(vmax) else 0.0,
        }
    return {
        "filename": filename,
        "dims": dict(ds.sizes),
        "variables": variables,
        "global_attrs": {k: str(v) for k, v in ds.attrs.items()},
    }


def to_geojson_points(
    filename: str,
    variable: str,
    time_idx: int = 0,
    depth_idx: int = 0,
    subsample: int = 2,
) -> dict:
    ds = open_netcdf(filename)
    if variable not in ds.data_vars:
        raise ValueError(f"Zmienna '{variable}' nie istnieje. Dostępne: {list(ds.data_vars)}")

    var = ds[variable]
    long_name = var.attrs.get("long_name", variable)
    units = var.attrs.get("units", "")

    # Redukuj do 2D przez kolejne isel
    reduce_dims = {}
    for dim in var.dims:
        dlow = dim.lower()
        if "time" in dlow:
            reduce_dims[dim] = min(time_idx, var.sizes[dim] - 1)
        elif any(k in dlow for k in ["depth", "level", "lev", "pressure", "plev", "z"]):
            reduce_dims[dim] = min(depth_idx, var.sizes[dim] - 1)
    if reduce_dims:
        var = var.isel(**reduce_dims)

    # Jeśli jeszcze więcej wymiarów — weź pierwsze
    while len(var.dims) > 2:
        var = var.isel({var.dims[0]: 0})

    data = var.values.astype(float)

    # Wykryj lat/lon
    lats = lons = None
    all_coords = {**dict(ds.coords), **dict(ds.data_vars)}
    for n in LAT_NAMES:
        if n in all_coords:
            lats = np.array(all_coords[n]); break
    for n in LON_NAMES:
        if n in all_coords:
            lons = np.array(all_coords[n]); break

    if lats is None or lons is None:
        # Ostatnia szansa — wymiary o nazwie podobnej do lat/lon
        for dim in var.dims:
            if dim.lower() in [x.lower() for x in LAT_NAMES] and dim in ds.coords:
                lats = ds.coords[dim].values
            if dim.lower() in [x.lower() for x in LON_NAMES] and dim in ds.coords:
                lons = ds.coords[dim].values

    if lats is None or lons is None:
        raise ValueError(
            f"Nie znaleziono współrzędnych geograficznych. "
            f"Dostępne coords: {list(ds.coords.keys())}"
        )

    # 1D vs 2D siatka
    if lats.ndim == 1 and lons.ndim == 1:
        lats_s = lats[::subsample]
        lons_s = lons[::subsample]
        data_s = data[::subsample, ::subsample]
        features = []
        for i, lat in enumerate(lats_s):
            for j, lon in enumerate(lons_s):
                if i >= data_s.shape[0] or j >= data_s.shape[1]:
                    continue
                val = float(data_s[i, j])
                if math.isnan(val): continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [round(float(lon), 5), round(float(lat), 5)]},
                    "properties": {"value": round(val, 4), "variable": variable, "units": units},
                })
    else:
        # Siatka 2D (curvilinear)
        lats_s = lats[::subsample, ::subsample]
        lons_s = lons[::subsample, ::subsample]
        data_s = data[::subsample, ::subsample]
        features = []
        for i in range(min(lats_s.shape[0], data_s.shape[0])):
            for j in range(min(lats_s.shape[1], data_s.shape[1])):
                val = float(data_s[i, j])
                if math.isnan(val): continue
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [round(float(lons_s[i,j]),5), round(float(lats_s[i,j]),5)]},
                    "properties": {"value": round(val, 4), "variable": variable, "units": units},
                })

    valid = data[~np.isnan(data)]
    vmin = float(np.min(valid)) if len(valid) else 0.0
    vmax = float(np.max(valid)) if len(valid) else 1.0

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "variable": variable,
            "long_name": long_name,
            "units": units,
            "count": len(features),
            "vmin": vmin,
            "vmax": vmax,
        },
    }
