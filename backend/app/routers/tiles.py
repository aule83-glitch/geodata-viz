"""
Serwer kafelków XYZ — generuje PNG tiles z danych rastrowych on-demand.
Używa rio-tiler do przycinania i renderowania GeoTIFF / NetCDF (po konwersji) do kafelków.
Kafelki mogą być ładowane bezpośrednio przez deck.gl / OpenLayers / MapLibre jako TileLayer.
"""

from io import BytesIO
from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/{filename}/{z}/{x}/{y}.png")
def get_tile(
    filename: str,
    z: int,
    x: int,
    y: int,
    colormap: str = Query("RdBu_r", description="Matplotlib colormap: RdBu_r, viridis, plasma, jet..."),
    vmin: float = Query(None),
    vmax: float = Query(None),
):
    """
    Zwraca kafelek PNG dla podanych współrzędnych {z}/{x}/{y}.
    Używaj jako URL warstwy w OpenLayers / MapLibre:
      http://localhost:8000/api/tiles/{filename}/{z}/{x}/{y}.png

    Wymaga pliku GeoTIFF w katalogu /data (przekonwertuj NC/GRIB2 wcześniej przez GDAL).
    """
    import os
    from pathlib import Path
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from PIL import Image

    try:
        from rio_tiler.io import Reader
    except ImportError:
        raise HTTPException(500, "rio-tiler nie jest zainstalowany.")

    DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
    path = DATA_DIR / filename

    if not path.exists():
        raise HTTPException(404, f"Plik nie istnieje: {filename}")

    try:
        with Reader(str(path)) as cog:
            img = cog.tile(x, y, z)
            data = img.data[0].astype(float)   # pierwsza banda
            mask = img.array.mask[0] if hasattr(img.array, "mask") else np.zeros_like(data, bool)
    except Exception as e:
        raise HTTPException(500, f"Błąd generowania kafelka: {e}")

    # Normalizacja
    _vmin = vmin if vmin is not None else float(np.nanmin(data[~mask]))
    _vmax = vmax if vmax is not None else float(np.nanmax(data[~mask]))
    norm = (data - _vmin) / (_vmax - _vmin + 1e-10)
    norm = np.clip(norm, 0, 1)

    # Kolorowanie
    cmap = cm.get_cmap(colormap)
    rgba = (cmap(norm) * 255).astype(np.uint8)
    rgba[mask, 3] = 0   # przezroczystość dla no-data

    buf = BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png", headers={
        "Cache-Control": "public, max-age=3600",
    })
