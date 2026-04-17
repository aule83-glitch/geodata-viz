import { useState, useEffect, useRef, useMemo } from 'react'
import maplibregl from 'maplibre-gl'
import { Deck } from '@deck.gl/core'
import { ScatterplotLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Sidebar } from './components/Sidebar'
import { Legend } from './components/Legend'
import { useGeoData } from './hooks/useGeoData'
import { getColorForValue } from './utils/colormap'

const INITIAL_VIEW = { longitude: 19.0, latitude: 52.0, zoom: 5, pitch: 0, bearing: 0 }

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const deckRef = useRef<Deck | null>(null)

  const [appState, setAppState] = useState<any>({
    selectedFile: null, selectedVariable: null, format: null,
    layerMode: 'scatter', colormap: 'viridis',
    opacity: 0.7, pointRadius: 5, subsample: 4
  })

  const { data, loading, error, metadata } = useGeoData(appState)

  // 1. MEMOIZACJA WARSTW - koniec z pętlą renderowania
  const layers = useMemo(() => {
    if (!data?.features?.length || !metadata) return []

    if (appState.layerMode === 'scatter') {
      return [new ScatterplotLayer({
        id: 'scatter',
        data: data.features,
        getPosition: (d: any) => d.geometry.coordinates,
        getFillColor: (d: any) => getColorForValue(d.properties.value, metadata.vmin, metadata.vmax, appState.colormap),
        getRadius: appState.pointRadius * 100,
        opacity: appState.opacity,
        pickable: true
      })]
    } else {
      return [new HeatmapLayer({
        id: 'heatmap',
        data: data.features,
        getPosition: (d: any) => d.geometry.coordinates,
        getWeight: (d: any) => {
          const range = metadata.vmax - metadata.vmin
          return range === 0 ? 0 : (d.properties.value - metadata.vmin) / range
        },
        radiusPixels: appState.pointRadius * 5,
        intensity: 1,
        threshold: 0.05,
        opacity: appState.opacity
      })]
    }
  }, [data, appState.layerMode, appState.colormap, appState.pointRadius, appState.opacity, metadata])

  // 2. INICJALIZACJA MAPY (tylko raz)
  useEffect(() => {
    if (!mapContainer.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [INITIAL_VIEW.longitude, INITIAL_VIEW.latitude],
      zoom: INITIAL_VIEW.zoom,
      interactive: true
    })

    const deck = new Deck({
      canvas: map.getCanvas(),
      initialViewState: INITIAL_VIEW,
      controller: true,
      style: { pointerEvents: 'none', backgroundColor: 'transparent' }, // FIX: przezroczystość
      onViewStateChange: ({viewState}: any) => {
        map.jumpTo({ center: [viewState.longitude, viewState.latitude], zoom: viewState.zoom })
      },
      layers: []
    })

    mapRef.current = map; deckRef.current = deck
    return () => { map.remove(); deck.finalize() }
  }, [])

  // 3. AKTUALIZACJA WARSTW
  useEffect(() => {
    if (deckRef.current) deckRef.current.setProps({ layers })
  }, [layers])

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', background: '#0a0e14' }}>
      <Sidebar appState={appState} setAppState={setAppState} loading={loading} error={error} metadata={metadata} />
      <div style={{ flex: 1, position: 'relative' }}>
        <div ref={mapContainer} style={{ position: 'absolute', inset: 0 }} />
        {metadata && <Legend metadata={metadata} colormap={appState.colormap} />}
      </div>
    </div>
  )
}
