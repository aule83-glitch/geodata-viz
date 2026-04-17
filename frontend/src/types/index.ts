export type Format = 'grib2' | 'netcdf' | 'hdf5'
export type LayerMode = 'scatter' | 'heatmap'
export type Colormap = 'viridis' | 'plasma' | 'RdBu_r' | 'coolwarm' | 'turbo' | 'inferno' | 'YlOrRd'

export interface AppState {
  selectedFile: string | null
  selectedVariable: string | null
  format: Format | null
  layerMode: LayerMode
  colormap: Colormap
  opacity: number
  pointRadius: number
  subsample: number
  timeIdx: number
  levelIdx: number
  // HDF5 only
  hdf5DatasetPath?: string
  hdf5LatPath?: string
  hdf5LonPath?: string
  scaleFactor?: number
  fillValue?: number
}

export interface FileInfo {
  name: string
  size_mb: number
  path: string
}

export interface VariableInfo {
  long_name: string
  units: string
  dims: string[]
  shape: number[]
  min: number
  max: number
}

export interface FileMetadata {
  filename: string
  format?: string
  dims?: Record<string, number>
  variables?: Record<string, VariableInfo>
  global_attrs?: Record<string, string>
  coords?: {
    lat_range?: [number, number]
    lon_range?: [number, number]
  }
  tree?: HDF5TreeItem[]
}

export interface HDF5TreeItem {
  path: string
  type: 'dataset' | 'group'
  shape?: number[]
  dtype?: string
  attrs?: Record<string, string>
}

export interface GeoJSONMetadata {
  variable: string
  units: string
  long_name: string
  count: number
  vmin: number
  vmax: number
  dataset_path?: string
  scale_factor_applied?: number | null
}

export interface GeoJSONResult {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
  metadata: GeoJSONMetadata
}

export interface GeoJSONFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: { value: number; variable: string; units: string }
}
