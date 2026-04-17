"""
GeoData Viz — FastAPI backend
Serwuje dane GRIB2, NetCDF, HDF5 jako GeoJSON / kafelki XYZ / JSON do frontendu.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import files, grib2, netcdf, hdf5, tiles

app = FastAPI(
    title="GeoData Viz API",
    description="Wizualizacja danych webowych, GRIB2, NetCDF, HDF5 na mapach dynamicznych.",
    version="0.1.0",
)

# Zezwól frontendowi (port 3000) na dostęp do API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router,  prefix="/api/files",  tags=["Pliki"])
app.include_router(grib2.router,  prefix="/api/grib2",  tags=["GRIB2"])
app.include_router(netcdf.router, prefix="/api/netcdf", tags=["NetCDF"])
app.include_router(hdf5.router,   prefix="/api/hdf5",   tags=["HDF5"])
app.include_router(tiles.router,  prefix="/api/tiles",  tags=["Kafelki XYZ"])


@app.get("/")
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "formats": ["GRIB2", "NetCDF", "HDF5"],
    }
