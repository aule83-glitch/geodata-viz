import os
import h5py
import numpy as np
from pyproj import Proj, Transformer
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))

def get_odim_params(f):
    """Wyciąga parametry projekcji i siatki ze standardu ODIM."""
    try:
        where = f['where'].attrs
        proj_str = where.get('projdef')
        if isinstance(proj_str, bytes): proj_str = proj_str.decode()
        
        x0 = float(where.get('xllcorner'))
        y0 = float(where.get('yllcorner'))
        dx = float(where.get('xscale'))
        dy = float(where.get('yscale'))

        # Jeśli wartości są małe, to są w km -> przeliczamy na metry dla pyproj
        if abs(x0) < 1000000:
            x0 *= 1000; y0 *= 1000; dx *= 1000; dy *= 1000
            
        return proj_str, x0, y0, dx, dy
    except Exception as e:
        logger.error(f"Błąd odczytu metadanych ODIM: {e}")
        return None

def hdf5_dataset_to_geojson(filename, dataset_path, subsample=4):
    path = DATA_DIR / filename.lstrip("/")
    with h5py.File(path, 'r') as f:
        odim = get_odim_params(f)
        if not odim: raise ValueError("To nie jest poprawny plik ODIM HDF5")
        
        proj_str, x0, y0, dx, dy = odim
        ds = f[dataset_path]
        data = ds[:]
        
        # Transformacja: Projekcja z pliku -> WGS84 (lat/lon)
        transformer = Transformer.from_proj(Proj(proj_str), Proj(proj="latlong", datum="WGS84"), always_xy=True)
        
        rows, cols = data.shape
        gain = ds.attrs.get('gain', 1.0)
        offset = ds.attrs.get('offset', 0.0)
        nodata = ds.attrs.get('nodata', 255)

        features = []
        for r in range(0, rows, subsample):
            for c in range(0, cols, subsample):
                val = data[r, c]
                if val == nodata: continue
                
                # Przeliczenie współrzędnych (r=0 to góra obrazu, więc odwracamy Y)
                x_curr = x0 + (c * dx)
                y_curr = y0 + ((rows - r) * dy)
                
                lon, lat = transformer.transform(x_curr, y_curr)
                
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                    "properties": {"value": float(val * gain + offset)}
                })

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "vmin": float(np.min(data[data != nodata] * gain + offset)) if np.any(data != nodata) else 0,
                "vmax": float(np.max(data[data != nodata] * gain + offset)) if np.any(data != nodata) else 1,
                "count": len(features)
            }
        }
