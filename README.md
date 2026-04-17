# GeoData Viz

Wizualizacja danych GRIB2, NetCDF, HDF5 na dynamicznych mapach OSM.
Uruchamia się jednym poleceniem na Windows 11 (Docker Desktop).

---

## Szybki start (Windows 11)

### Wymagania
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — instalacja zajmuje ~5 minut, nie wymaga WSL

### Uruchomienie

**Opcja A — terminal (PowerShell / CMD):**
```cmd
docker compose up --build
```

Po uruchomieniu otwórz przeglądarkę:
- **Aplikacja:** http://localhost:3000
- **API / dokumentacja:** http://localhost:8000/docs

---

## Wgrywanie danych

### Metoda 1 — skopiuj plik do katalogu `backend/data/`

```
geodata-viz/
└── backend/
    └── data/
        ├── era5_temperature.grib2   ← tutaj
        ├── sst_global.nc            ← tutaj
        └── MOD11A1.hdf5             ← tutaj
```

Obsługiwane rozszerzenia:

| Format | Rozszerzenia |
|--------|-------------|
| GRIB2  | `.grib2`, `.grb2`, `.grb`, `.grib` |
| NetCDF | `.nc`, `.nc4`, `.netcdf`, `.cdf` |
| HDF5   | `.h5`, `.hdf5`, `.hdf`, `.he5` |

### Metoda 2 — HTTP upload przez API

```bash
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@moj_plik.grib2"
```

Lub przez interfejs Swagger UI: http://localhost:8000/docs → `POST /api/files/upload`

---

## Jak używać aplikacji

1. **Wybierz plik** z listy po lewej stronie
2. **Wybierz zmienną** (GRIB2/NetCDF) lub **ścieżkę datasetu** (HDF5)
3. Ustaw **tryb warstwy**: Scatter (punkty) lub Heatmap
4. Wybierz **paletę kolorów** i dostosuj parametry
5. Najeżdżaj myszką na punkty — zobaczysz wartość w tooltipie

### Parametry

| Parametr | Opis |
|----------|------|
| Subsampling | Co N-ty punkt ładowany z API (1=wszystkie, 4=co 4.) |
| Promień | Rozmiar punktu na mapie (scatter mode) |
| Indeks czasu | Krok czasowy (0=pierwszy) |
| Indeks poziomu | Poziom ciśnienia/głębokość (0=powierzchnia) |

---

## Przykłady danych do testów

### ERA5 (GRIB2) — temperatura 2m
Pobierz z [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/):
- Zmienna: `2m_temperature` → plik `.grib` / `.grib2`
- Po wgraniu: wybierz zmienną `t2m`, paleta `RdBu_r`

### NOAA SST (NetCDF) — temperatura powierzchni oceanu
```bash
# Darmowy plik testowy (ERA5-like):
wget https://downloads.psl.noaa.gov/Datasets/noaa.ersst.v5/sst.mnmean.nc
```
- Zmienna: `sst`, paleta: `plasma`

### NASA MODIS LST (HDF5) — temperatura powierzchni lądu
Pobierz z [NASA EarthData](https://earthdata.nasa.gov/):
- Produkt: `MOD11A1` (dzienne LST, 1km)
- Dataset path: `/MODIS_Grid_Daily_1km_LST/Data Fields/LST_Day_1km`
- Scale factor: `0.02`, fill value: `0`

---

## Architektura

```
frontend (React + deck.gl + MapLibre) :3000
    ↕ HTTP / GeoJSON
backend (FastAPI + Python)            :8000
    ↕ cfgrib / netCDF4 / h5py
backend/data/ (pliki GRIB2/NC/HDF5)
```

---

## API — główne endpointy

```
GET  /api/files/                          # lista wszystkich plików
POST /api/files/upload                    # wgranie pliku

GET  /api/grib2/{file}/info               # metadane GRIB2
GET  /api/grib2/{file}/geojson?variable=t2m&subsample=4

GET  /api/netcdf/{file}/info              # metadane NetCDF
GET  /api/netcdf/{file}/geojson?variable=sst

GET  /api/hdf5/{file}/info                # drzewo struktury HDF5
GET  /api/hdf5/{file}/geojson?dataset_path=/Grid/LST&scale_factor=0.02

GET  /api/tiles/{file}/{z}/{x}/{y}.png    # kafelki XYZ z GeoTIFF
```

---

## Zatrzymanie aplikacji

```cmd
docker compose down
```

Lub naciśnij `Ctrl+C` w terminalu, a następnie:
```cmd
docker compose down
```

---

## Dalszy rozwój

- [ ] Eksport do GeoTIFF / GeoJSON
- [ ] Animacja kroków czasowych
- [ ] Izolinie (contour lines) z danych rastrowych
- [ ] Wektorowe dane wiatru (U/V components → strzałki)
- [ ] WMS/WMTS jako warstwa bazowa lub nakładka
- [ ] Profil pionowy (kliknij punkt → wykres wartości vs głębokość)
