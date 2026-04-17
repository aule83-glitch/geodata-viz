import { getGradientCSS } from '../utils/colormap'
import type { GeoJSONMetadata } from '../types'
import type { Colormap } from '../types'

interface LegendProps {
  metadata: GeoJSONMetadata
  colormap: Colormap
}

export function Legend({ metadata, colormap }: LegendProps) {
  return (
    <div style={{
      position: 'absolute', bottom: 40, left: 16,
      background: 'rgba(10,14,20,0.88)',
      border: '1px solid #1e2d3d',
      borderRadius: 4, padding: '10px 12px', minWidth: 200,
      fontFamily: '"IBM Plex Mono", monospace',
    }}>
      <div style={{ fontSize: 10, color: '#4a6a8a', letterSpacing: 1, marginBottom: 6 }}>
        {metadata.long_name || metadata.variable}
        {metadata.units ? ` [${metadata.units}]` : ''}
      </div>
      <div style={{
        height: 10, borderRadius: 2,
        background: getGradientCSS(colormap),
        marginBottom: 4,
      }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#7eb8f7' }}>
        <span>{metadata.vmin?.toFixed(2)}</span>
        <span>{((metadata.vmin + metadata.vmax) / 2).toFixed(2)}</span>
        <span>{metadata.vmax?.toFixed(2)}</span>
      </div>
    </div>
  )
}


