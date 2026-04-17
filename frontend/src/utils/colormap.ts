import type { Colormap } from '../types'

// Palety kolorów (RGBA) zaimplementowane lokalnie — bez zależności od d3
// Każda paleta to 8 stopów interpolowanych liniowo

const PALETTES: Record<Colormap, number[][]> = {
  viridis: [
    [68,1,84],[72,40,120],[62,83,160],[49,120,157],
    [35,156,149],[53,183,121],[109,205,89],[180,222,44],[253,231,37]
  ],
  plasma: [
    [13,8,135],[84,2,163],[139,10,165],[185,50,137],
    [219,92,104],[244,136,73],[254,188,43],[240,249,33]
  ],
  inferno: [
    [0,0,4],[40,11,84],[101,21,110],[159,42,99],
    [212,72,66],[245,125,21],[252,185,57],[252,255,164]
  ],
  turbo: [
    [48,18,59],[86,83,209],[51,167,224],[18,212,159],
    [138,230,68],[240,210,22],[255,144,14],[214,38,40]
  ],
  RdBu_r: [
    [103,0,31],[178,24,43],[214,96,77],[244,165,130],
    [209,229,240],[146,197,222],[67,147,195],[33,102,172],[5,48,97]
  ],
  coolwarm: [
    [59,76,192],[98,130,234],[141,176,254],[184,208,249],
    [220,220,220],[249,197,174],[239,130,103],[205,67,51],[180,4,38]
  ],
  YlOrRd: [
    [255,255,204],[255,237,160],[254,217,118],[254,178,76],
    [253,141,60],[252,78,42],[227,26,28],[189,0,38],[128,0,38]
  ],
}

export const COLORMAPS = Object.keys(PALETTES) as Colormap[]

function lerp(a: number, b: number, t: number) {
  return Math.round(a + (b - a) * t)
}

/**
 * Zwraca kolor RGBA [r,g,b,a] dla wartości znormalizowanej do [0,1].
 */
export function getColorForValue(
  value: number,
  vmin: number,
  vmax: number,
  colormap: Colormap,
): [number, number, number, number] {
  const palette = PALETTES[colormap] ?? PALETTES.viridis
  const t = Math.max(0, Math.min(1, (value - vmin) / (vmax - vmin + 1e-10)))
  const scaled = t * (palette.length - 1)
  const idx = Math.min(Math.floor(scaled), palette.length - 2)
  const frac = scaled - idx
  const c0 = palette[idx]
  const c1 = palette[idx + 1]
  return [
    lerp(c0[0], c1[0], frac),
    lerp(c0[1], c1[1], frac),
    lerp(c0[2], c1[2], frac),
    255,
  ]
}

/**
 * Zwraca gradient CSS do legendy.
 */
export function getGradientCSS(colormap: Colormap, reverse = false): string {
  const palette = PALETTES[colormap] ?? PALETTES.viridis
  const stops = (reverse ? [...palette].reverse() : palette)
    .map((c, i) => `rgb(${c[0]},${c[1]},${c[2]}) ${Math.round((i / (palette.length - 1)) * 100)}%`)
    .join(', ')
  return `linear-gradient(to right, ${stops})`
}
