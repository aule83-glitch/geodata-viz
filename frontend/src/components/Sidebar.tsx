import type { AppState, Format } from '../types'
import { useFileList, useFileInfo } from '../hooks/useGeoData'
import { COLORMAPS } from '../utils/colormap'

interface Props {
  appState: AppState
  setAppState: React.Dispatch<React.SetStateAction<AppState>>
  loading: boolean
  error: string | null
  metadata: any
}

const C = {
  sidebar: { width: 290, minWidth: 290, height: '100vh', background: '#0d1117', borderRight: '1px solid #1e2d3d',
    display: 'flex', flexDirection: 'column' as const, overflow: 'hidden', fontFamily: '"IBM Plex Mono", monospace', color: '#c8d8e8' },
  header: { padding: '16px 16px 12px', borderBottom: '1px solid #1e2d3d', background: '#0a0e14' },
  title: { fontSize: 13, fontWeight: 700, color: '#7eb8f7', letterSpacing: 3, margin: 0 },
  sub: { fontSize: 10, color: '#4a6a8a', letterSpacing: 1, marginTop: 3 },
  scroll: { flex: 1, overflowY: 'auto' as const, padding: '0 0 24px' },
  section: { padding: '12px 16px 10px', borderBottom: '1px solid #1a2535' },
  label: { fontSize: 10, color: '#4a6a8a', letterSpacing: 2, marginBottom: 6, display: 'block' },
  select: { width: '100%', background: '#131c28', border: '1px solid #1e2d3d', color: '#c8d8e8',
    fontSize: 11, padding: '6px 8px', borderRadius: 3, fontFamily: '"IBM Plex Mono", monospace',
    outline: 'none', cursor: 'pointer', boxSizing: 'border-box' as const },
  input: { width: '100%', background: '#131c28', border: '1px solid #1e2d3d', color: '#c8d8e8',
    fontSize: 11, padding: '6px 8px', borderRadius: 3, fontFamily: '"IBM Plex Mono", monospace',
    outline: 'none', boxSizing: 'border-box' as const },
  row: { display: 'flex', gap: 8, alignItems: 'center', marginTop: 6 },
  slider: { flex: 1, accentColor: '#7eb8f7' },
  val: { fontSize: 11, color: '#7eb8f7', minWidth: 32, textAlign: 'right' as const },
  tab: (a: boolean) => ({ flex: 1, padding: '5px 0', fontSize: 10, letterSpacing: 1,
    background: a ? '#1e2d3d' : 'transparent', border: '1px solid ' + (a ? '#7eb8f7' : '#1e2d3d'),
    color: a ? '#7eb8f7' : '#4a6a8a', cursor: 'pointer', borderRadius: 2,
    fontFamily: '"IBM Plex Mono", monospace' }),
  error: { margin: '10px 16px', padding: '8px', background: '#1a0e0e', border: '1px solid #5a1a1a',
    borderRadius: 3, fontSize: 10, color: '#ff6b6b', wordBreak: 'break-word' as const },
  meta: { margin: '10px 16px', padding: '8px', background: '#0d1a24', border: '1px solid #1e2d3d', borderRadius: 3 },
  mr: { display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 3 },
  mk: { color: '#4a6a8a' }, mv: { color: '#7eb8f7' },
  empty: { fontSize: 10, color: '#4a6a8a', lineHeight: 1.7 },
  hint: { fontSize: 10, color: '#4a6a8a', marginTop: 4, lineHeight: 1.5 },
}

export function Sidebar({ appState, setAppState, loading, error, metadata }: Props) {
  const { files } = useFileList()
  const { info } = useFileInfo(appState.selectedFile, appState.format)

  const set = (patch: Partial<AppState>) => setAppState(s => ({ ...s, ...patch }))

  const allFiles = [
    ...(files?.grib2  ?? []).map((f: any) => ({ ...f, format: 'grib2'  as Format })),
    ...(files?.netcdf ?? []).map((f: any) => ({ ...f, format: 'netcdf' as Format })),
    ...(files?.hdf5   ?? []).map((f: any) => ({ ...f, format: 'hdf5'   as Format })),
  ]

  const variables = info?.variables ? Object.keys(info.variables) : []

  // ODIM: spłaszcz wszystkie data_fields ze wszystkich datasets
  const odimFields: { path: string; label: string }[] = []
  if (info?.odim && info?.datasets) {
    for (const ds of info.datasets) {
      for (const df of ds.data_fields ?? []) {
        const label = [ds.group, df.quantity || df.path.split('/').pop()].filter(Boolean).join(' › ')
        odimFields.push({ path: df.path, label })
      }
    }
  }

  // Generic HDF5: datasety z drzewa
  const hdf5Datasets = (!info?.odim && info?.tree)
    ? info.tree.filter((t: any) => t.type === 'dataset' && t.shape?.length >= 2)
    : []

  return (
    <div style={C.sidebar}>
      <div style={C.header}>
        <p style={C.title}>GEODATA VIZ</p>
        <p style={C.sub}>GRIB2 · NETCDF · HDF5 (ODIM) → OSM</p>
      </div>

      <div style={C.scroll}>
        {/* Wybór pliku */}
        <div style={C.section}>
          <span style={C.label}>PLIK DANYCH</span>
          {allFiles.length === 0 ? (
            <div style={C.empty}>
              Brak plików. Wgraj plik do<br />
              <span style={{ color: '#7eb8f7' }}>backend/data/</span><br />
              lub przez <span style={{ color: '#7eb8f7' }}>POST /api/files/upload</span>
            </div>
          ) : (
            <select style={C.select} value={appState.selectedFile ?? ''}
              onChange={e => {
                const f = allFiles.find(x => x.name === e.target.value)
                set({ selectedFile: e.target.value || null, format: f?.format ?? null,
                      selectedVariable: null, hdf5DatasetPath: undefined })
              }}>
              <option value="">— wybierz plik —</option>
              {allFiles.map(f => (
                <option key={f.name} value={f.name}>
                  [{f.format.toUpperCase()}] {f.name} ({f.size_mb} MB)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* GRIB2 / NetCDF — zmienna */}
        {(appState.format === 'grib2' || appState.format === 'netcdf') && (
          <div style={C.section}>
            <span style={C.label}>ZMIENNA</span>
            <select style={C.select} value={appState.selectedVariable ?? ''}
              onChange={e => set({ selectedVariable: e.target.value || null })}>
              <option value="">— wybierz zmienną —</option>
              {variables.map(v => {
                const vi = info.variables[v]
                return <option key={v} value={v}>{v} — {vi.long_name?.slice(0, 28)} [{vi.units}]</option>
              })}
            </select>
            {appState.selectedVariable && info?.variables?.[appState.selectedVariable] && (
              <div style={C.hint}>
                Kształt: {info.variables[appState.selectedVariable].shape.join(' × ')}
              </div>
            )}
          </div>
        )}

        {/* ODIM HDF5 — wybór pola z listy */}
        {appState.format === 'hdf5' && info?.odim && (
          <div style={C.section}>
            <span style={C.label}>POLE DANYCH (ODIM)</span>
            {odimFields.length > 0 ? (
              <>
                <select style={C.select} value={appState.hdf5DatasetPath ?? ''}
                  onChange={e => set({ hdf5DatasetPath: e.target.value || undefined })}>
                  <option value="">— wybierz pole —</option>
                  {odimFields.map(f => (
                    <option key={f.path} value={f.path}>{f.label}</option>
                  ))}
                </select>
                <div style={C.hint}>
                  Projekcja: {info.projdef?.slice(0, 50)}<br />
                  Siatka: {info.xsize} × {info.ysize} px
                </div>
              </>
            ) : (
              <div style={C.empty}>Brak pól danych w pliku ODIM.</div>
            )}
          </div>
        )}

        {/* Generic HDF5 — dataset path */}
        {appState.format === 'hdf5' && !info?.odim && (
          <div style={C.section}>
            <span style={C.label}>DATASET PATH</span>
            {hdf5Datasets.length > 0 ? (
              <select style={C.select} value={appState.hdf5DatasetPath ?? ''}
                onChange={e => set({ hdf5DatasetPath: e.target.value || undefined })}>
                <option value="">— wybierz dataset —</option>
                {hdf5Datasets.map((d: any) => (
                  <option key={d.path} value={d.path}>
                    {d.path} [{d.shape?.join('×')}]
                  </option>
                ))}
              </select>
            ) : (
              <input style={C.input} placeholder="/Grid/temperature"
                value={appState.hdf5DatasetPath ?? ''}
                onChange={e => set({ hdf5DatasetPath: e.target.value || undefined })} />
            )}
            <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              <div>
                <span style={{ ...C.label, marginBottom: 3 }}>Scale factor</span>
                <input style={C.input} type="number" step="0.001" placeholder="np. 0.02"
                  value={appState.scaleFactor ?? ''}
                  onChange={e => set({ scaleFactor: e.target.value ? Number(e.target.value) : undefined })} />
              </div>
              <div>
                <span style={{ ...C.label, marginBottom: 3 }}>Fill value</span>
                <input style={C.input} type="number" placeholder="np. 65535"
                  value={appState.fillValue ?? ''}
                  onChange={e => set({ fillValue: e.target.value ? Number(e.target.value) : undefined })} />
              </div>
            </div>
          </div>
        )}

        {/* Tryb warstwy */}
        <div style={C.section}>
          <span style={C.label}>TRYB WARSTWY</span>
          <div style={{ display: 'flex', gap: 6 }}>
            {(['scatter', 'heatmap'] as const).map(m => (
              <button key={m} style={C.tab(appState.layerMode === m)} onClick={() => set({ layerMode: m })}>
                {m === 'scatter' ? 'PUNKTY' : 'HEATMAPA'}
              </button>
            ))}
          </div>
        </div>

        {/* Paleta */}
        <div style={C.section}>
          <span style={C.label}>PALETA KOLORÓW</span>
          <select style={C.select} value={appState.colormap}
            onChange={e => set({ colormap: e.target.value as any })}>
            {COLORMAPS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Parametry */}
        <div style={C.section}>
          <span style={C.label}>PARAMETRY</span>
          {[
            { label: 'Przezroczystość', key: 'opacity', min: 0.1, max: 1, step: 0.05, fmt: (v: number) => Math.round(v*100)+'%' },
            { label: appState.layerMode === 'scatter' ? 'Promień punktu' : 'Promień heatmapy', key: 'pointRadius', min: 1, max: 50, step: 1, fmt: (v: number) => String(v) },
            { label: 'Subsampling (co N-ty)', key: 'subsample', min: 1, max: 20, step: 1, fmt: (v: number) => String(v) },
            { label: 'Indeks czasu', key: 'timeIdx', min: 0, max: 99, step: 1, fmt: (v: number) => String(v) },
          ].map(({ label, key, min, max, step, fmt }) => (
            <div key={key} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 10, color: '#4a6a8a', marginBottom: 2 }}>{label}</div>
              <div style={C.row}>
                <input type="range" min={min} max={max} step={step}
                  value={(appState as any)[key]} style={C.slider}
                  onChange={e => set({ [key]: Number(e.target.value) } as any)} />
                <span style={C.val}>{fmt((appState as any)[key])}</span>
              </div>
            </div>
          ))}
          {(appState.format === 'grib2' || appState.format === 'netcdf') && (
            <div>
              <div style={{ fontSize: 10, color: '#4a6a8a', marginBottom: 2 }}>Indeks poziomu</div>
              <div style={C.row}>
                <input type="range" min={0} max={99} step={1} value={appState.levelIdx} style={C.slider}
                  onChange={e => set({ levelIdx: Number(e.target.value) })} />
                <span style={C.val}>{appState.levelIdx}</span>
              </div>
            </div>
          )}
        </div>

        {error && <div style={C.error}>⚠ {error}</div>}

        {metadata && (
          <div style={C.meta}>
            <div style={{ fontSize: 10, color: '#4a6a8a', letterSpacing: 2, marginBottom: 6 }}>METADANE</div>
            {[
              ['zmienna', metadata.variable ?? metadata.dataset_path?.split('/').pop()],
              ['opis', metadata.long_name],
              ['jednostki', metadata.units || '—'],
              ['min', metadata.vmin?.toFixed(4)],
              ['max', metadata.vmax?.toFixed(4)],
              ['punktów', metadata.count?.toLocaleString()],
            ].map(([k, v]) => v ? (
              <div key={k} style={C.mr}>
                <span style={C.mk}>{k}</span>
                <span style={{ ...C.mv, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v}</span>
              </div>
            ) : null)}
          </div>
        )}
      </div>
    </div>
  )
}
