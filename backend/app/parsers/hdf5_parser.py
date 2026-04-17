import h5py
import numpy as np
from pyproj import Proj, Transformer
from pathlib import Path

def get_odim_metadata(f):
    """Wyciąga parametry projekcji ze standardu ODIM."""
    where = f['where'].attrs
    # projdef to np. "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m"
    proj_str = where.get('projdef').decode() if isinstance(where.get('projdef'), bytes) else where.get('projdef')
    
    # ODIM podaje corner w km lub m - musimy to ujednolicić
    x_corner = where.get('xllcorner')
    y_corner = where.get('yllcorner')
    x_size = where.get('xscale')
    y_size = where.get('yscale')
    
    # Jeśli wartości są małe (np. rzędu 3000-5000), to są to km -> zamień na metry
    if abs(x_corner) < 100000: x_corner *= 1000; y_corner *= 1000; x_size *= 1000; y_size *= 1000
    
    return proj_str, x_corner, y_corner, x_size, y_size

def hdf5_odim_to_geojson(filename, dataset_path, subsample=4):
    path = DATA_DIR / filename
    with h5py.File(path, 'r') as f:
        proj_str, x0, y0, dx, dy = get_odim_metadata(f)
        ds = f[dataset_path]
        data = ds[:]
        
        # Przygotowanie transformacji: Projekcja Lokalna -> WGS84
        in_proj = Proj(proj_str)
        out_proj = Proj(init='epsg:4321') # Lat/Lon
        transformer = Transformer.from_proj(in_proj, out_proj)
        
        rows, cols = data.shape
        features = []
        
        # Skalowanie i offset (z atrybutów datasetu - gain/offset)
        gain = ds.attrs.get('gain', 1.0)
        offset = ds.attrs.get('offset', 0.0)
        nodata = ds.attrs.get('nodata', 255)

        for r in range(0, rows, subsample):
            for c in range(0, cols, subsample):
                val = data[r, c]
                if val == nodata: continue
                
                real_val = val * gain + offset
                
                # OBLICZENIE XY: r to wiersz (Y), c to kolumna (X)
                # W ODIM yllcorner to dół, ale r=0 to góra obrazu. Odwracamy r.
                x_curr = x0 + (c * dx)
                y_curr = y0 + ((rows - r) * dy) # Odwrócenie osi Y
                
                lon, lat = transformer.transform(x_curr, y_curr)
                
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {"value": float(real_val)}
                })
        
        return {"type": "FeatureCollection", "features": features}
