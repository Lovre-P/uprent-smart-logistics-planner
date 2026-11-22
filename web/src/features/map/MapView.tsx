import { useEffect, useId, useRef, useState } from 'react'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { formatKg, formatKm } from '../../lib/format'
import { truckColor } from '../../lib/plan'
import type { Location, Scenario, SolveResult, StepView } from '../../types'
import './map.css'

const number = new Intl.NumberFormat('hr-HR', {maximumSignificantDigits: 8})
const actionName = {PICKUP: 'Utovar', DELIVERY: 'Istovar', RETURN: 'Povratak u bazu'}
type Point = { x: number; y: number }

function projection(locations: Location[], width: number, height: number) {
  const left = 45, top = 32, right = width - 40, bottom = height - 43
  const xs = locations.map(l => l.x), ys = locations.map(l => l.y)
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys)
  const scale = Math.min((right - left) / Math.max(1, maxX - minX), (bottom - top) / Math.max(1, maxY - minY))
  const cx = (left + right) / 2, cy = (top + bottom) / 2
  const xMiddle = (maxX + minX) / 2, yMiddle = (maxY + minY) / 2
  const x = (value: number) => cx + (value - xMiddle) * scale
  const y = (value: number) => cy - (value - yMiddle) * scale
  const rough = 50 / scale
  const power = 10 ** Math.floor(Math.log10(rough))
  const interval = ([1, 2, 5, 10].find(m => m * power >= rough) ?? 10) * power
  const ticks = (low: number, high: number) => {
    const first = Math.ceil(low / interval), last = Math.floor(high / interval)
    return Array.from({length: Math.max(0, last - first + 1)}, (_, i) => (first + i) * interval)
  }
  return {
    x, y, left, right, top, bottom,
    xTicks: ticks(xMiddle + (left - cx) / scale, xMiddle + (right - cx) / scale),
    yTicks: ticks(yMiddle + (cy - bottom) / scale, yMiddle + (cy - top) / scale),
  }
}

function describe(truck: string, step: StepView) {
  return [
    truck + ', korak ' + step.seq,
    actionName[step.action] + (step.order ? ' ' + step.order + ' (' + step.machine + ')' : ''),
    step.location, step.arrive,
    'dionica ' + formatKm(step.leg_km), 'teret ' + formatKg(step.load_kg),
  ].join(' · ')
}

export function MapView({scenario, result}: {scenario: Scenario; result: SolveResult}) {
  const container = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(620)
  const [selection, setSelection] = useState<{truck: string; seq: number} | null>(null)
  const group = useId()
  useEffect(() => {
    const frame = container.current
    if (!frame || typeof ResizeObserver === 'undefined') return
    const resize = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setWidth(Math.max(240, Math.round(entry.contentRect.width)))
    })
    resize.observe(frame)
    return () => resize.disconnect()
  }, [])

  const height = width < 480 ? 340 : 390
  const plot = projection(scenario.locations, width, height)
  const points = new Map(scenario.locations.map(l => [l.id, {x:plot.x(l.x), y:plot.y(l.y)}]))
  const samePlace = new Map<string, Location[]>()
  for (const location of scenario.locations) {
    const key = location.x + ',' + location.y
    const group = samePlace.get(key)
    if (group) group.push(location)
    else samePlace.set(key, [location])
  }
  const depot = points.get(scenario.depot)!
  const routes = result.trucks.filter(truck => truck.used)
  const selectedTruck = routes.find(t => t.id === selection?.truck) ?? routes[0]
  const selectedStep = selectedTruck?.steps.find(s => s.seq === selection?.seq) ?? selectedTruck?.steps[0]
  // A separate numbered badge for every visit, including actions at the same coordinates.
  const visits = new Map<string, number>()
  const locateBadge = (point: Point): Point => {
    const key = point.x + ',' + point.y
    const visit = visits.get(key) ?? 0
    visits.set(key, visit + 1)
    const side = point.x > width - 85 ? -1 : 1
    const sign = point.y > height - 70 ? -1 : 1
    return {x:point.x + side * (10 + (visit % 4) * 17), y:point.y + sign * (10 + Math.floor(visit / 4) * 17)}
  }
  return <section className="route-map" aria-label="Karta ruta">
    <InfoLine>{hints.tabs.map}</InfoLine>
    <div className="route-map__panel">
      <ul className="route-map__legend" aria-label="Kamioni na karti">
        {scenario.trucks.map(truck => {
          const route = result.trucks.find(t => t.id === truck.id)
          return <li key={truck.id}><span style={{background:truckColor(truck.id)}} />
            <strong>{truck.name || truck.id}</strong>
            {route?.used ? formatKm(route.km) : 'u bazi'}
          </li>
        })}
      </ul>
      <div ref={container} className="route-map__canvas">
        <svg viewBox={`0 0 ${width} ${height}`} role="group" aria-label="Koordinate lokacija i smjer vožnje">
          <defs>{routes.map((truck, index) => <marker key={truck.id} id={group + '-arrow-' + index}
            viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto">
            <path d="M0 0 L10 5 L0 10 L2.5 5 Z" fill={truckColor(truck.id)} />
          </marker>)}</defs>
          {plot.xTicks.map(t => <g className={'map-tick' + (t === 0 ? ' map-tick--origin' : '')} key={'x' + t}>
            <line x1={plot.x(t)} x2={plot.x(t)} y1={plot.top - 16} y2={plot.bottom + 12} />
            <text x={plot.x(t)} y={height - 12} textAnchor="middle">{number.format(t)}</text>
          </g>)}
          {plot.yTicks.map(t => <g className={'map-tick' + (t === 0 ? ' map-tick--origin' : '')} key={'y' + t}>
            <line x1={plot.left - 12} x2={plot.right + 16} y1={plot.y(t)} y2={plot.y(t)} />
            <text x={plot.left - 18} y={plot.y(t) + 3} textAnchor="end">{number.format(t)}</text>
          </g>)}
          <text className="map-axis" x="7" y="14">Y (km)</text>
          <text className="map-axis" x={width - 4} y={height - 12} textAnchor="end">X (km)</text>
          {routes.map((truck, index) => {
            let previous = depot
            return <g key={truck.id} data-testid={'route-' + truck.id} aria-label={'Ruta: ' + truck.name}>
              {truck.steps.map(step => {
                const start = previous
                const end = points.get(step.location)!
                previous = end
                if (start.x === end.x && start.y === end.y) return null
                const mid = `${(start.x + end.x) / 2},${(start.y + end.y) / 2}`
                return <polyline key={step.seq} points={`${start.x},${start.y} ${mid} ${end.x},${end.y}`}
                  fill="none" stroke={truckColor(truck.id)} strokeWidth="2" strokeLinejoin="round"
                  markerMid={`url(#${group}-arrow-${index})`} />
              })}
            </g>
          })}
          {Array.from(samePlace.values(), locations => {
            const p = points.get(locations[0].id)!
            const isDepot = locations.some(l => l.id === scenario.depot)
            return <g key={locations[0].id} transform={`translate(${p.x} ${p.y})`}>
              <title>{locations.map(l => l.name || l.id).join(' / ')} ({number.format(locations[0].x)}, {number.format(locations[0].y)})</title>
              {isDepot ? <rect x="-5" y="-5" width="10" height="10" rx="1" className="map-depot" />
                : <circle r="4" className="map-location" />}
              <text className="map-label" x={p.x > width - 80 ? -7 : 7} y="-7" textAnchor={p.x > width - 80 ? 'end' : 'start'}>
                {locations.map((l, i) => <tspan key={l.id} data-testid={'loc-' + l.id} data-x={p.x} data-y={p.y}>
                  {i > 0 ? ' / ' : ''}{l.id}
                </tspan>)}{isDepot ? ' · Baza' : ''}
              </text>
            </g>
          })}
          {routes.flatMap(truck => truck.steps.map(step => {
            const badge = locateBadge(points.get(step.location)!)
            const selected = truck.id === selectedTruck?.id && step.seq === selectedStep?.seq
            const select = () => setSelection({truck:truck.id, seq:step.seq})
            return <g key={truck.id + '-' + step.seq} className="map-step" role="button" tabIndex={0}
              aria-label={describe(truck.name, step)} aria-pressed={selected}
              transform={`translate(${badge.x} ${badge.y})`} onFocus={select} onClick={select} onMouseEnter={select}
              onKeyDown={e => {if (e.key === 'Enter' || e.key === ' ') {e.preventDefault(); select()}}}>
              <circle r="7.5" fill={truckColor(truck.id)} />
              <text textAnchor="middle" dy=".34em">{step.seq}</text>
            </g>
          }))}
        </svg>
      </div>
      <p role="status" className="route-map__detail">{selectedTruck && selectedStep
        ? describe(selectedTruck.name, selectedStep) : 'Svi kamioni ostaju u bazi.'}</p>
    </div>
  </section>
}
