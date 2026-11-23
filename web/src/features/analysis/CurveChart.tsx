import { useState } from 'react'
import { formatDuration, formatKm } from '../../lib/format'
import type { Analysis, Settings } from '../../types'

type Point = Analysis['curve'][number]
const numeric = new Intl.NumberFormat('hr-HR', {maximumFractionDigits: 1})

export function CurveChart({points, currentKm, applySettings, busy, empty}: {
  points: Point[]; currentKm: number; applySettings: (patch: Partial<Settings>) => void; busy?: boolean; empty: string
}) {
  const [hovered, setHovered] = useState<Point | null>(null)
  const focused = hovered && points.includes(hovered) ? hovered : points.find(p => p.km === currentKm) ?? points[0]
  function apply(point: Point) {
    if (busy) return
    const pins = Object.fromEntries(Object.entries(point.by_truck).flatMap(([tid, orders]) => orders.map(oid => [oid, tid])))
    applySettings({pinned_orders: pins})
  }
  if (!focused) return <section className="analysis-card"><h3>Udaljenost i kraj radnog dana</h3><p>{empty}</p></section>
  const kms = points.map(p => p.km)
  const ends = points.map(p => p.end_min)
  const left = 60, right = 474, top = 27, bottom = 180
  const minKm = Math.min(...kms), maxKm = Math.max(...kms)
  const minEnd = Math.min(...ends), maxEnd = Math.max(...ends)
  const x = (km: number) => maxKm === minKm ? (left + right) / 2 : left + (km-minKm)/(maxKm-minKm)*(right-left)
  const y = (end: number) => maxEnd === minEnd ? (top + bottom) / 2 : bottom - (end-minEnd)/(maxEnd-minEnd)*(bottom-top)
  const fractions = maxEnd === minEnd ? [0] : [0, .5, 1]
  return <section className="analysis-card"><h3>Udaljenost i kraj radnog dana</h3>
    <svg className="analysis-curve" viewBox="0 0 512 226" aria-label="Krivulja kilometraže i trajanja radnog dana">
      <text x={left} y="13">Kraj radnog dana (min)</text>
      {fractions.map(fraction => {
        const end = minEnd + fraction * (maxEnd-minEnd)
        return <g key={fraction}><line x1={left} x2={right} y1={y(end)} y2={y(end)} className="curve-grid"/>
          <text x={left-9} y={y(end)+4} textAnchor="end">{numeric.format(end)}</text></g>
      })}
      <line className="curve-axis" x1={left} x2={right} y1={bottom} y2={bottom}/>
      {[...new Set([minKm,maxKm])].map(km => <text key={km} x={x(km)} y={bottom+16} textAnchor="middle">{formatKm(km)}</text>)}
      <text x={(left+right)/2} y="217" textAnchor="middle">Ukupna udaljenost (km)</text>
      <polyline className="curve-line" points={points.map(p => x(p.km)+','+y(p.end_min)).join(' ')}/>
      {points.map(point => {
        const label = formatKm(point.km) + ', ' + numeric.format(point.end_min) + ' min'
        return <g key={point.km} role="button" tabIndex={busy ? -1 : 0} aria-disabled={busy}
          aria-label={'Prikaži raspored: ' + label} className="curve-point"
          onFocus={() => setHovered(point)} onBlur={() => setHovered(null)}
          onMouseEnter={() => setHovered(point)} onMouseLeave={() => setHovered(null)}
          onClick={() => apply(point)} onKeyDown={event => {
            if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); apply(point) }
          }}>
          <title>{label}</title><circle cx={x(point.km)} cy={y(point.end_min)} r={9} fill="transparent"/>
          <circle className={point === focused ? 'curve-dot is-focused' : 'curve-dot'}
            cx={x(point.km)} cy={y(point.end_min)} r={point === focused ? 5 : 3.5}/>
        </g>
      })}
    </svg>
    <div className="curve-readout"><strong>{formatKm(focused.km)}</strong><span>Radni dan {formatDuration(focused.end_min)}</span></div>
  </section>
}
