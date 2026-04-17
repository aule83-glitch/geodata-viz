import { useState, useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import { Deck } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Sidebar } from './components/Sidebar'
import { Legend } from './components/Legend'
import { StatusBar } from './components/StatusBar'
import { useGeoData } from './hooks/useGeoData'
import { getColorForValue } from './utils/colormap'
import type { AppState } from './types'

const INIT = { longitude: 19.0, latitude: 52.0, zoom: 5, bearing: 0, pitch: 0 }

// OSM jako wbudowany styl (bez zewnętrznych CDN)
const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap' },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

export default function App() {
  const mapDiv   = useRef<HTMLDivElement>(null)
  const mapRef   = useRef<maplibregl.Map | null>(null)
  const deckRef  = useRef<Deck | null>(null)
  const vsRef    = useRef(INIT)

  const [appState, setAppState] = useState<AppState>({
    selectedFile: null, selectedVariable: null, format: null,
    layerMode: 'scatter', colormap: 'viridis',
    opacity: 0.8, pointRadius: 6, subsample: 4, timeIdx: 0, levelIdx: 0,
  })

  const [hover, setHover]       = useState<{ x: number; y: number; value: number; units: string } | null>(null)
  const [initErr, setInitErr]   = useState<string | null>(null)

  const { data, loading, error, metadata } = useGeoData(appState)

  /* ── Inicjalizacja mapy + deck.gl ── */
  useEffect(() => {
    if (!mapDiv.current) return

    let map: maplibregl.Map
    let deck: Deck

    try {
      map = new maplibregl.Map({
        container: mapDiv.current,
        style: OSM_STYLE,
        center: [INIT.longitude, INIT.latitude],
        zoom: INIT.zoom,
        interactive: false,        // deck.gl przejmuje kontrolę
      })
      map.addControl(new maplibregl.NavigationControl(), 'top-right')
      map.addControl(new maplibregl.ScaleControl(), 'bottom-right')
      mapRef.current = map

      deck = new Deck({
        canvas: map.getCanvas(),
        width: '100%', height: '100%',
        initialViewState: { ...INIT, minZoom: 1, maxZoom: 20 },
        controller: true,
        layers: [],
        style: { background: 'transparent', position: 'absolute' },
        onViewStateChange: ({ viewState }: any) => {
          vsRef.current = viewState
          map.jumpTo({
            center: [viewState.longitude, viewState.latitude],
            zoom: viewState.zoom,
            bearing: viewState.bearing,
            pitch: viewState.pitch,
          })
        },
      })
      deckRef.current = deck
    } catch (e: any) {
      setInitErr(e?.message ?? String(e))
    }

    return () => {
      try { deck?.finalize() } catch (_) {}
      try { map?.remove()   } catch (_) {}
    }
  }, [])

  /* ── Aktualizacja warstw ── */
  useEffect(() => {
    if (!deckRef.current) return

    const layers: any[] = []

    if (data?.features?.length) {
      const vmin = metadata?.vmin ?? 0
      const vmax = metadata?.vmax ?? 1

      if (appState.layerMode === 'scatter') {
        layers.push(new ScatterplotLayer({
          id: 'scatter',
          data: data.features,
          getPosition: (f: any) => f.geometry.coordinates,
          getRadius: appState.pointRadius * 500,
          getFillColor: (f: any) => getColorForValue(f.properties.value, vmin, vmax, appState.colormap),
          radiusMinPixels: 2,
          radiusMaxPixels: 30,
          pickable: true,
          opacity: appState.opacity,
          onHover: (info: any) => setHover(info.object
            ? { x: info.x, y: info.y, value: info.object.properties.value, units: info.object.properties.units ?? metadata?.units ?? '' }
            : null),
          updateTriggers: { getFillColor: [vmin, vmax, appState.colormap], getRadius: [appState.pointRadius] },
        }))
      } else {
        layers.push(new HeatmapLayer({
          id: 'heatmap',
          data: data.features,
          getPosition: (f: any) => f.geometry.coordinates,
          getWeight: (f: any) => {
            const v = f.properties.value
            if (isNaN(v)) return 0
            const norm = (v - vmin) / (vmax - vmin + 1e-10)
            return Math.max(0, Math.min(1, norm))
          },
          radiusPixels: 30,
          intensity: 2,
          threshold: 0.03,
          opacity: appState.opacity,
        }))
      }
    }

    deckRef.current.setProps({ layers })
  }, [data, metadata, appState.layerMode, appState.colormap, appState.opacity, appState.pointRadius])

  if (initErr) return (
    <div style={{ color: '#ff6b6b', padding: 40, fontFamily: 'monospace', background: '#0a0e14', minHeight: '100vh' }}>
      <h2>Błąd inicjalizacji mapy</h2>
      <pre style={{ marginTop: 16, color: '#c8d8e8' }}>{initErr}</pre>
    </div>
  )

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', background: '#0a0e14', fontFamily: '"IBM Plex Mono", monospace' }}>
      <Sidebar appState={appState} setAppState={setAppState} loading={loading} error={error} metadata={metadata} />
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div ref={mapDiv} style={{ position: 'absolute', inset: 0 }} />
        {hover && (
          <div style={{ position: 'absolute', left: hover.x + 14, top: hover.y - 12,
            background: 'rgba(10,14,20,0.93)', border: '1px solid #2a3a4a', borderRadius: 4,
            padding: '5px 10px', color: '#c8d8e8', fontSize: 12, pointerEvents: 'none', zIndex: 100 }}>
            <span style={{ color: '#7eb8f7' }}>{hover.value.toFixed(3)}</span>
            {hover.units ? ' ' + hover.units : ''}
          </div>
        )}
        {loading && (
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(10,14,20,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20 }}>
            <span style={{ color: '#7eb8f7', letterSpacing: 3, fontSize: 13 }}>ŁADOWANIE…</span>
          </div>
        )}
        {metadata && <Legend metadata={metadata} colormap={appState.colormap} />}
        <StatusBar data={data} metadata={metadata} />
      </div>
    </div>
  )
}
