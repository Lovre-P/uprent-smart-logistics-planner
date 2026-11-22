import { useState, type CSSProperties } from 'react'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { formatDuration, formatKm } from '../../lib/format'
import { truckColor } from '../../lib/plan'
import type { Order, Scenario, Settings, SolveResult, TruckView } from '../../types'
import './timeline.css'

type Segment = { kind: 'drive' | 'load' | 'unload'; start: number; minutes: number; description: string }
const decimal = new Intl.NumberFormat('hr-HR', {maximumFractionDigits:3})
const minutesLabel = (minutes: number) => decimal.format(minutes) + ' min'
const percent = (minutes: number, extent: number) => (100 * minutes / extent) + '%'

function routeSegments(truck: TruckView, speed: number, depot: string, orders: Map<string, Order>, settings: Settings) {
  const segments: Segment[] = []
  let elapsed = 0, previous = depot
  for (const step of truck.steps) {
    if (step.leg_km > 0) {
      const minutes = step.leg_km * 60 / speed
      segments.push({kind:'drive', start:elapsed, minutes,
        description:`Vožnja ${previous} → ${step.location} · ${formatKm(step.leg_km)} · ${minutesLabel(minutes)}`})
      elapsed += minutes
    }
    if (step.action !== 'RETURN') {
      const order = orders.get(step.order!)!
      const loading = step.action === 'PICKUP'
      const minutes = loading ? (order.load_min ?? settings.load_min) : (order.unload_min ?? settings.unload_min)
      const action = loading ? 'Utovar' : 'Istovar'
      segments.push({kind:loading ? 'load' : 'unload', start:elapsed, minutes,
        description:`${action} ${step.order} (${step.machine}) · ${step.location} · ${step.arrive}–${step.depart} · ${minutesLabel(minutes)}`})
      elapsed += minutes
    }
    previous = step.location
  }
  return {segments, elapsed}
}

function clockLabel(start: string, after: number) {
  const [hour, minute] = start.split(':').map(Number)
  const value = hour * 60 + minute + Math.floor(after)
  const current = value % 1440
  const clock = String(Math.floor(current / 60)).padStart(2, '0') + ':' + String(current % 60).padStart(2, '0')
  return value >= 1440 ? clock + ' (+' + Math.floor(value / 1440) + ' d)' : clock
}

function TruckTimeline({truck, segments, extent, ticks, start}: {
  truck: TruckView; segments: Segment[]; extent: number; ticks: number[]; start: string
}) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const active = activeIndex === null ? undefined : segments[activeIndex]
  const driveLimit = truck.limit_basis === 'drive'
  const vars = {'--route-color':truckColor(truck.id)} as CSSProperties
  return <article className="time-truck" aria-label={truck.name} style={vars}>
    <header className="time-truck__header">
      <h3><span />{truck.name}</h3>
      {truck.used ? <span>{start} – {truck.steps.at(-1)?.depart} · {formatDuration(truck.total_min)}</span> : <span>Ostaje u bazi</span>}
    </header>
    {truck.used && <>
      <div className="time-truck__work">
        <div className="time-truck__axis" aria-label="Satnica radnog dana">
          {ticks.map(t => <span className="time-tick" key={t} style={{left:percent(t, extent)}}>
            {clockLabel(start, t)}
          </span>)}
        </div>
        <div className="time-truck__rail" aria-label="Slijed vožnje, utovara i istovara">
          {segments.map((segment, index) => <button type="button" key={index}
            className={'time-segment time-segment--' + segment.kind + (segment.minutes === 0 ? ' time-segment--zero' : '')}
            style={{left:percent(segment.start, extent), width:percent(segment.minutes, extent)}}
            data-minutes={segment.minutes} aria-label={segment.description} title={segment.description}
            onFocus={() => setActiveIndex(index)} onMouseEnter={() => setActiveIndex(index)} onClick={() => setActiveIndex(index)} />)}
          {!driveLimit && <span data-testid="limit-work" className="time-limit" style={{left:percent(truck.limit_min, extent)}} />}
        </div>
        <p className="time-truck__detail" role="status">{active?.description ??
          `Vožnja ${formatDuration(truck.drive_min)} · Radnje ${formatDuration(truck.handling_min)}`}</p>
      </div>
      <div className="time-truck__limit">
        <div className="time-truck__limit-text">
          <span><i aria-hidden="true"/>Dnevni limit · {driveLimit ? 'samo vožnja' : 'vožnja i radnje'}</span>
          <strong>{formatDuration(driveLimit ? truck.drive_min : truck.total_min)} od {formatDuration(truck.limit_min)}</strong>
        </div>
        {driveLimit && <div className="time-truck__gauge" aria-label="Iskorišteno vrijeme vožnje">
          <span className="time-truck__used" style={{width:percent(truck.drive_min, Math.max(truck.limit_min, truck.drive_min))}} />
          <span data-testid="limit-drive" className="time-limit" style={{left:percent(truck.limit_min, Math.max(truck.limit_min, truck.drive_min))}}/>
        </div>}
      </div>
    </>}
  </article>
}

export function TimelineView({scenario, result}: {scenario: Scenario; result: SolveResult}) {
  const orders = new Map(scenario.orders.map(order => [order.id, order]))
  const trucks = new Map(scenario.trucks.map(truck => [truck.id, truck]))
  const timelines = result.trucks.map(truck => ({truck, ...routeSegments(truck, trucks.get(truck.id)!.speed_kmh,
    scenario.depot, orders, result.settings)}))
  const maximum = Math.max(1, ...timelines.map(({truck, elapsed}) =>
    truck.used && truck.limit_basis === 'drive+handling' ? Math.max(truck.limit_min, elapsed) : elapsed))
  const interval = [1, 2, 5, 10, 15, 30, 60, 120, 180, 240, 360, 720, 1440].find(n => n >= maximum / 4)
    ?? Math.ceil(maximum / 4 / 1440) * 1440
  const extent = Math.ceil(maximum / interval) * interval
  const ticks = Array.from({length:Math.round(extent / interval) + 1}, (_, i) => i * interval)
  return <section className="time-view" aria-label="Vremenska crta">
    <InfoLine>{hints.tabs.timeline}</InfoLine>
    <ul className="time-legend" aria-label="Vrste segmenata">
      <li><i className="time-key--drive"/>Vožnja</li>
      <li><i className="time-key--load"/>Utovar</li>
      <li><i className="time-key--unload"/>Istovar</li>
    </ul>
    {timelines.map(({truck, segments}) => <TruckTimeline key={truck.id} truck={truck} segments={segments}
      extent={extent} ticks={ticks} start={result.settings.day_start}/>)}
  </section>
}
