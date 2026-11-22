import { useState } from 'react'
import { ChevronDown, Truck } from 'lucide-react'
import { formatDuration, formatKg, formatKm } from '../../lib/format'
import { truckColor } from '../../lib/plan'
import type { TruckView } from '../../types'
import { StepTable } from './StepTable'

export function TruckCard({ truck, depot, explanation }: {truck:TruckView; depot:string; explanation?:string}) {
  const [expanded, setExpanded] = useState(false)
  const title=truck.name || truck.id
  const route=[depot,...truck.steps.map(step=>step.location)].filter((place,i,all)=>!i || place!==all[i-1])
  return <article className={'truck-card'+(!truck.used?' truck-card--idle':'')} aria-label={title}>
    <div className="truck-header">
      <span className="truck-symbol" style={{color:truckColor(truck.id)}}><Truck size={21} aria-hidden="true"/></span>
      <h3>{title}</h3>{truck.used ? <span className="truck-km">{formatKm(truck.km)}</span> : <span>nije korišten · 0 km</span>}
      {!truck.used && <button className="why-button" onClick={()=>setExpanded(v=>!v)} aria-expanded={expanded} type="button">
        Zašto?<ChevronDown size={14} aria-hidden="true"/></button>}
    </div>
    {!truck.used && expanded && <p className="truck-explanation">{explanation ?? 'Kamion ostaje u bazi jer mu u ovom planu nije dodijeljen nalog.'}</p>}
    {truck.used && <>
      <dl className="truck-facts">
        <div><dt>Izvršeni nalozi</dt><dd>{truck.orders.length}</dd></div>
        <div><dt>Vožnja</dt><dd>{formatDuration(truck.drive_min)}</dd></div>
        <div><dt>Utovar i istovar</dt><dd>{formatDuration(truck.handling_min)}</dd></div>
        <div><dt>Radni dan</dt><dd>{formatDuration(truck.total_min)}</dd></div>
        <div><dt>Rezerva do limita</dt><dd>{formatDuration(truck.slack_min)}</dd></div>
        <div><dt>Najveći teret</dt><dd>{formatKg(truck.peak_kg)} / {formatKg(truck.capacity_kg)} ({(100 * truck.peak_kg / truck.capacity_kg).toLocaleString('hr-HR', {maximumFractionDigits:1})} %)</dd></div>
        <div><dt>Zauzeta mjesta najviše</dt><dd>{truck.peak_slots} / {truck.slots}</dd></div>
      </dl>
      <p className="truck-route"><strong>Ruta</strong> {route.join(' → ')}</p>
      <StepTable truck={truck}/>
    </>}
  </article>
}
