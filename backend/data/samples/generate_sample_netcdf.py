"""
Generuje przykładowy plik NetCDF z syntetycznymi danymi temperatury.
Przydatny do testowania wizualizacji bez potrzeby pobierania prawdziwych danych.

Uruchomienie:
    pip install netCDF4 numpy
    python generate_sample_netcdf.py
"""

import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta

OUTPUT = "sample_temperature.nc"

# Siatka 1°×1° dla Europy + Atlantyku
lats = np.arange(30.0, 75.0, 1.0)   # 45 punktów
lons = np.arange(-30.0, 50.0, 1.0)  # 80 punktów
times = [datetime(2024, 1, 1) + timedelta(hours=6*i) for i in range(4)]

ds = nc.Dataset(OUTPUT, "w", format="NETCDF4")

# Wymiary
ds.createDimension("time", len(times))
ds.createDimension("lat", len(lats))
ds.createDimension("lon", len(lons))

# Zmienne współrzędnych
t_var = ds.createVariable("time", "f8", ("time",))
t_var.units = "hours since 2024-01-01 00:00:00"
t_var.calendar = "standard"
t_var[:] = nc.date2num(times, t_var.units, t_var.calendar)

lat_var = ds.createVariable("lat", "f4", ("lat",))
lat_var.units = "degrees_north"
lat_var.long_name = "latitude"
lat_var[:] = lats

lon_var = ds.createVariable("lon", "f4", ("lon",))
lon_var.units = "degrees_east"
lon_var.long_name = "longitude"
lon_var[:] = lons

# Temperatura 2m — syntetyczne pole z gradientem N-S + zaburzeniem
temp = ds.createVariable("t2m", "f4", ("time", "lat", "lon"), fill_value=-9999.0)
temp.units = "K"
temp.long_name = "2 metre temperature"
temp.standard_name = "air_temperature"

LON, LAT = np.meshgrid(lons, lats)
for i in range(len(times)):
    base = 280.0 - 0.4 * (LAT - 52)          # gradient N-S
    wave = 5.0 * np.sin(np.radians(LON) * 2 + i * 0.5)  # fala zachodnia
    noise = np.random.normal(0, 1.5, LAT.shape)
    temp[i, :, :] = base + wave + noise

# Ciśnienie przyziemne
slp = ds.createVariable("msl", "f4", ("time", "lat", "lon"))
slp.units = "Pa"
slp.long_name = "Mean sea level pressure"
slp[:] = 101325 + 1500 * np.sin(np.radians(LAT) * 2)[np.newaxis, :, :] + \
         np.random.normal(0, 200, (len(times), len(lats), len(lons)))

# Atrybuty globalne
ds.title = "Synthetic meteorological data for testing GeoData Viz"
ds.institution = "GeoData Viz test generator"
ds.source = "Synthetic"
ds.history = f"Created {datetime.now().isoformat()}"
ds.Conventions = "CF-1.8"

ds.close()
print(f"Zapisano: {OUTPUT}")
print(f"Wymiary: time={len(times)}, lat={len(lats)}, lon={len(lons)}")
print(f"Zmienne: t2m (temperatura 2m), msl (ciśnienie)")
print(f"Skopiuj plik do backend/data/ i wybierz w aplikacji.")
