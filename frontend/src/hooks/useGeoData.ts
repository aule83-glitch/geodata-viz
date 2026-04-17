import { useState, useEffect } from 'react'
import type { AppState, GeoJSONResult, GeoJSONMetadata } from '../types'

const API = '/api'

export function useGeoData(state: AppState) {
  const [data, setData] = useState<GeoJSONResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<GeoJSONMetadata | null>(null)

  useEffect(() => {
    if (!state.selectedFile || !state.format) return

    // GRIB2 / NetCDF potrzebuje wybranej zmiennej
    if ((state.format === 'grib2' || state.format === 'netcdf') && !state.selectedVariable) return

    // HDF5 potrzebuje ścieżki do datasetu
    if (state.format === 'hdf5' && !state.hdf5DatasetPath) return

    const ctrl = new AbortController()

    async function fetchData() {
      setLoading(true)
      setError(null)

      try {
        let url = ''
        const params = new URLSearchParams()

        if (state.format === 'grib2') {
          url = `${API}/grib2/${state.selectedFile}/geojson`
          params.set('variable', state.selectedVariable!)
          params.set('time_idx', String(state.timeIdx))
          params.set('level_idx', String(state.levelIdx))
          params.set('subsample', String(state.subsample))
        } else if (state.format === 'netcdf') {
          url = `${API}/netcdf/${state.selectedFile}/geojson`
          params.set('variable', state.selectedVariable!)
          params.set('time_idx', String(state.timeIdx))
          params.set('depth_idx', String(state.levelIdx))
          params.set('subsample', String(state.subsample))
        } else if (state.format === 'hdf5') {
          url = `${API}/hdf5/${state.selectedFile}/geojson`
          params.set('dataset_path', state.hdf5DatasetPath!)
          if (state.hdf5LatPath) params.set('lat_path', state.hdf5LatPath)
          if (state.hdf5LonPath) params.set('lon_path', state.hdf5LonPath)
          params.set('time_idx', String(state.timeIdx))
          params.set('subsample', String(state.subsample))
          if (state.scaleFactor != null) params.set('scale_factor', String(state.scaleFactor))
          if (state.fillValue != null) params.set('fill_value', String(state.fillValue))
        }

        const res = await fetch(`${url}?${params}`, { signal: ctrl.signal })
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }))
          throw new Error(err.detail || `HTTP ${res.status}`)
        }

        const json: GeoJSONResult = await res.json()
        setData(json)
        setMetadata(json.metadata)
      } catch (e: any) {
        if (e.name === 'AbortError') return
        setError(e.message)
        setData(null)
        setMetadata(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    return () => ctrl.abort()
  }, [
    state.selectedFile, state.selectedVariable, state.format,
    state.timeIdx, state.levelIdx, state.subsample,
    state.hdf5DatasetPath, state.hdf5LatPath, state.hdf5LonPath,
    state.scaleFactor, state.fillValue,
  ])

  return { data, loading, error, metadata }
}

// Hook do pobierania listy plików
export function useFileList() {
  const [files, setFiles] = useState<{ grib2: any[]; netcdf: any[]; hdf5: any[] } | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/files/`)
      .then(r => r.json())
      .then(setFiles)
      .catch(() => setFiles({ grib2: [], netcdf: [], hdf5: [] }))
      .finally(() => setLoading(false))
  }, [])

  return { files, loading }
}

// Hook do pobierania metadanych pliku (info o zmiennych)
export function useFileInfo(filename: string | null, format: string | null) {
  const [info, setInfo] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!filename || !format) { setInfo(null); return }
    setLoading(true)
    fetch(`/api/${format}/${filename}/info`)
      .then(r => r.json())
      .then(setInfo)
      .catch(() => setInfo(null))
      .finally(() => setLoading(false))
  }, [filename, format])

  return { info, loading }
}
