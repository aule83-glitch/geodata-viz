"""
Parser HDF5 — obsługuje dwa warianty:

1. ODIM HDF5 (standard IMGW/EUMETSAT) — dane radarowe z projekcją kartograficzną.
   Parser przelicza siatkę XY → lat/lon przez pyproj.

2. NASA/naukowe HDF5 — z datasetami lat/lon wprost w pliku.
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional
import h5py

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))


def list_hdf5_files() -> list[dict]:
    exts = {".h5", ".hdf5", ".hdf", ".he5"}
    files = []
    for f in DATA_DIR.rglob("*"):
        if f.suffix.lower() in exts:
            files.append({
                "name": str(f.relative_to(DATA_DIR)),
                "size_mb": round(f.stat().st_size / 1_048_576, 2),
                "path": str(f),
            })
    return files


def _dec(v):
    if isinstance(v, (bytes, np.bytes_)):
        return v.tobytes().decode("utf-8", errors="replace")
    return v


def _attr(obj, key, default=None):
    if key not in obj.attrs:
        return default
    return _dec(obj.attrs[key])


def _walk(group: h5py.Group, prefix="") -> list[dict]:
    items = []
    for name, item in group.items():
        path = f"{prefix}/{name}"
        try:
            attrs = {k: str(_dec(v)) for k, v in item.attrs.items()}
            if isinstance(item, h5py.Dataset):
                items.append({"path": path, "type": "dataset",
                               "shape": list(item.shape), "dtype": str(item.dtype), "attrs": attrs})
            elif isinstance(item, h5py.Group):
                items.append({"path": path, "type": "group", "attrs": attrs})
                items.extend(_walk(item, path))
        except Exception:
            pass
    return items


def _is_odim(f: h5py.File) -> bool:
    conv = str(_attr(f, "Conventions", ""))
    if "ODIM" in conv:
        return True
    return "what" in f and "where" in f and any(k.startswith("dataset") for k in f.keys())


def get_hdf5_info(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    with h5py.File(str(path), "r") as f:
        root_attrs = {k: str(_dec(v)) for k, v in f.attrs.items()}
        odim = _is_odim(f)
        tree = _walk(f)

        odim_info = {}
        if odim and "where" in f:
            wh = f["where"]
            datasets = []
            for key in sorted(f.keys()):
                if not key.startswith("dataset"):
                    continue
                grp = f[key]
                ds_what = {k: str(_dec(v)) for k, v in grp.get("what", {}).attrs.items()} if "what" in grp else {}
                data_fields = []
                for dkey in sorted(grp.keys()):
                    if not dkey.startswith("data"):
                        continue
                    d_grp = grp[dkey]
                    d_what = {k: str(_dec(v)) for k, v in d_grp.get("what", {}).attrs.items()} if "what" in d_grp else {}
                    if "data" in d_grp:
                        data_fields.append({
                            "path": f"/{key}/{dkey}/data",
                            "quantity": d_what.get("quantity", dkey),
                            "gain": d_what.get("gain", "1"),
                            "offset": d_what.get("offset", "0"),
                            "nodata": d_what.get("nodata", ""),
                            "undetect": d_what.get("undetect", ""),
                            "units": d_what.get("units", ""),
                        })
                datasets.append({
                    "group": key,
                    "product": ds_what.get("product", ""),
                    "quantity": ds_what.get("quantity", ""),
                    "data_fields": data_fields,
                })

            odim_info = {
                "odim": True,
                "projdef": _attr(wh, "projdef", ""),
                "xsize": int(wh.attrs.get("xsize", 0)),
                "ysize": int(wh.attrs.get("ysize", 0)),
                "xscale": float(wh.attrs.get("xscale", 1)),
                "yscale": float(wh.attrs.get("yscale", 1)),
                "xllcorner": float(wh.attrs.get("xllcorner", 0)),
                "yllcorner": float(wh.attrs.get("yllcorner", 0)),
                "datasets": datasets,
            }

    return {"filename": filename, "format": "ODIM_HDF5" if odim else "HDF5",
            "root_attrs": root_attrs, "tree": tree, **odim_info}


def _odim_grid_to_latlon(projdef, xsize, ysize, xscale, yscale, xllcorner, yllcorner, subsample):
    from pyproj import CRS, Transformer

    proj_str = projdef if "+proj=" in projdef else projdef
    try:
        crs_src = CRS.from_proj4(proj_str)
    except Exception:
        crs_src = CRS.from_string(proj_str)

    transformer = Transformer.from_crs(crs_src, CRS.from_epsg(4326), always_xy=True)

    xs_full = xllcorner + np.arange(xsize) * xscale + xscale / 2.0
    if yscale < 0:
        ys_full = yllcorner + (ysize - 1 - np.arange(ysize)) * abs(yscale) + abs(yscale) / 2.0
    else:
        ys_full = yllcorner + np.arange(ysize) * yscale + yscale / 2.0

    XX, YY = np.meshgrid(xs_full[::subsample], ys_full[::subsample])
    lons_2d, lats_2d = transformer.transform(XX, YY)
    return lats_2d, lons_2d


def hdf5_dataset_to_geojson(
    filename: str,
    dataset_path: str,
    lat_path: Optional[str] = None,
    lon_path: Optional[str] = None,
    time_idx: int = 0,
    subsample: int = 4,
    scale_factor: Optional[float] = None,
    fill_value: Optional[float] = None,
) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {path}")

    with h5py.File(str(path), "r") as f:
        if _is_odim(f):
            return _odim_to_geojson(f, dataset_path, subsample)
        else:
            return _generic_hdf5_to_geojson(f, dataset_path, lat_path, lon_path,
                                             time_idx, subsample, scale_factor, fill_value)


def _odim_to_geojson(f: h5py.File, dataset_path: str, subsample: int) -> dict:
    wh = f["where"]
    projdef   = _attr(wh, "projdef", "")
    xsize     = int(wh.attrs["xsize"])
    ysize     = int(wh.attrs["ysize"])
    xscale    = float(wh.attrs["xscale"])
    yscale    = float(wh.attrs["yscale"])
    xllcorner = float(wh.attrs["xllcorner"])
    yllcorner = float(wh.attrs["yllcorner"])

    if not projdef:
        raise ValueError("Brak projdef w /where")
    if dataset_path not in f:
        raise ValueError(f"Dataset '{dataset_path}' nie istnieje")

    raw = f[dataset_path][...].astype(float)

    # gain/offset/nodata z siostrzanej grupy /what
    parts = [p for p in dataset_path.strip("/").split("/") if p]
    what_path = "/" + "/".join(parts[:-1]) + "/what"
    gain = 1.0; offset = 0.0; nodata = None; undetect = None
    quantity = ""; units = ""
    if what_path in f:
        w = f[what_path]
        gain      = float(w.attrs.get("gain",      1.0))
        offset    = float(w.attrs.get("offset",    0.0))
        nodata    = float(w.attrs.get("nodata",    -9999.0))
        undetect  = float(w.attrs.get("undetect",  0.0))
        quantity  = str(_dec(w.attrs.get("quantity", "")))
        units     = str(_dec(w.attrs.get("units",    "")))

    lats_2d, lons_2d = _odim_grid_to_latlon(
        projdef, xsize, ysize, xscale, yscale, xllcorner, yllcorner, subsample
    )

    data_s = raw[::subsample, ::subsample]
    rows = min(lats_2d.shape[0], data_s.shape[0])
    cols = min(lats_2d.shape[1], data_s.shape[1])

    features = []
    valid_vals = []
    for i in range(rows):
        for j in range(cols):
            rv = data_s[i, j]
            if nodata is not None and rv == nodata:
                continue
            if undetect is not None and rv == undetect:
                continue
            val = rv * gain + offset
            lat = float(lats_2d[i, j])
            lon = float(lons_2d[i, j])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            valid_vals.append(val)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]},
                "properties": {"value": round(float(val), 4), "variable": quantity, "units": units},
            })

    vmin = float(np.min(valid_vals)) if valid_vals else 0.0
    vmax = float(np.max(valid_vals)) if valid_vals else 1.0
    return {
        "type": "FeatureCollection", "features": features,
        "metadata": {
            "variable": quantity, "dataset_path": dataset_path,
            "units": units, "long_name": quantity,
            "count": len(features), "vmin": vmin, "vmax": vmax,
        },
    }


def _generic_hdf5_to_geojson(f, dataset_path, lat_path, lon_path,
                               time_idx, subsample, scale_factor, fill_value):
    if dataset_path not in f:
        raise ValueError(f"Dataset '{dataset_path}' nie istnieje")
    ds = f[dataset_path]
    data = ds[...].astype(float)
    if data.ndim == 3:
        data = data[time_idx]

    attrs = {k: str(_dec(v)) for k, v in ds.attrs.items()}
    if scale_factor is None and "scale_factor" in ds.attrs:
        scale_factor = float(ds.attrs["scale_factor"])
    if fill_value is None and "_FillValue" in ds.attrs:
        fill_value = float(ds.attrs["_FillValue"])

    lats = lons = None
    for n in (["lat","latitude","Latitude","LAT","nav_lat"]):
        if (lat_path and lat_path in f):
            lats = f[lat_path][...]; break
        if n in f:
            lats = f[n][...]; break
    for n in (["lon","longitude","Longitude","LON","nav_lon"]):
        if (lon_path and lon_path in f):
            lons = f[lon_path][...]; break
        if n in f:
            lons = f[n][...]; break

    if lats is None or lons is None:
        raise ValueError("Nie znaleziono lat/lon. Podaj lat_path i lon_path.")

    if fill_value is not None:
        data[data == fill_value] = np.nan
    if scale_factor is not None:
        data = data * scale_factor

    c2 = lats.ndim == 2
    lats_s = lats[::subsample, ::subsample] if c2 else lats[::subsample]
    lons_s = lons[::subsample, ::subsample] if c2 else lons[::subsample]
    data_s = data[::subsample, ::subsample]
    rows, cols = data_s.shape[:2]

    features = []
    for i in range(rows):
        for j in range(cols):
            val = float(data_s[i, j])
            if np.isnan(val): continue
            lat = float(lats_s[i,j] if c2 else lats_s[i])
            lon = float(lons_s[i,j] if c2 else lons_s[j])
            features.append({"type":"Feature",
                "geometry":{"type":"Point","coordinates":[lon,lat]},
                "properties":{"value":round(val,4),"variable":dataset_path.split("/")[-1],"units":attrs.get("units","")}})

    valid = data[~np.isnan(data)]
    return {"type":"FeatureCollection","features":features,"metadata":{
        "variable":dataset_path.split("/")[-1],"dataset_path":dataset_path,
        "units":attrs.get("units",""),"long_name":attrs.get("long_name",dataset_path),
        "count":len(features),"vmin":float(valid.min()) if len(valid) else 0.0,
        "vmax":float(valid.max()) if len(valid) else 1.0,"scale_factor_applied":scale_factor}}
