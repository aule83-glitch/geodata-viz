import type { GeoJSONMetadata } from '../types'

interface StatusBarProps {
  data: any
  metadata: GeoJSONMetadata | null
}

export function StatusBar({ data, metadata }: StatusBarProps) {
  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0,
      background: 'rgba(10,14,20,0.85)',
      borderTop: '1px solid #1e2d3d',
      padding: '4px 16px',
      display: 'flex', gap: 24, alignItems: 'center',
      fontFamily: '"IBM Plex Mono", monospace', fontSize: 10, color: '#4a6a8a',
    }}>
      <span>© OpenStreetMap contributors</span>
      {metadata && (
        <>
          <span style={{ color: '#1e2d3d' }}>|</span>
          <span>
            <span style={{ color: '#7eb8f7' }}>{metadata.count?.toLocaleString()}</span> punktów
          </span>
          <span style={{ color: '#1e2d3d' }}>|</span>
          <span>
            {metadata.variable ?? metadata.dataset_path?.split('/').pop()}
            {metadata.units ? ` [${metadata.units}]` : ''}
          </span>
        </>
      )}
    </div>
  )
}
