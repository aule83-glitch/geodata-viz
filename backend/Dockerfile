FROM python:3.12-slim

# GDAL + eccodes (wymagane dla GRIB2)
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    gdal-bin \
    libeccodes-dev \
    libeccodes-tools \
    libhdf5-dev \
    libnetcdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
