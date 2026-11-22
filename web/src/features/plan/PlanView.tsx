import { LoaderCircle, Route, ClipboardCheck, Truck } from 'lucide-react'
import { Callout } from '../../components/Callout'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { formatKm } from '../../lib/format'
import { hasUsablePlan } from '../../lib/plan'
import type { Scenario, Settings, SolveResult } from '../../types'
import { AlternativeStrip } from './AlternativeStrip'
import { TruckCard } from './TruckCard'
import { Warnings } from './Warnings'
import './plan.css'

interface Props {
  result:SolveResult|null
  scenario:Scenario
  applySettings:(settings:Partial<Settings>)=>void
  onOrder?:(id:string)=>void
  onDetailed?:()=>void
  computing?:boolean
  error?:string|null
}
export function PlanView({result,scenario,applySettings,onOrder,onDetailed,computing=false,error}:Props) {
  const usable=!!result && hasUsablePlan(result)
  const status=result && (!result.validation.passed ? 'INVALID_PLAN' : result.status)
  const stale=computing || !!error
  return <div className="plan-view">
    <InfoLine>{hints.tabs.plan}</InfoLine>
    {computing && <p className="computing-line" role="status"><LoaderCircle size={15} aria-hidden="true"/>Računam…</p>}
    {error && <Callout tone="error">{error}{result && ' Prikazan je posljednji uspješan izračun.'}</Callout>}
    {result && !usable && status && <Callout tone={status==='INVALID_PLAN'?'error':'warning'}>
      <strong>{hints.status[status].title}</strong><p>{hints.status[status].body}</p>
    </Callout>}
    {result && usable && <>
      <section className="plan-metrics" aria-label="Sažetak plana">
        <div className="metric-primary"><span><Route size={17} aria-hidden="true"/>Ukupna udaljenost</span><strong>{formatKm(result.totals.km)}</strong></div>
        <div><span><ClipboardCheck size={17} aria-hidden="true"/>Izvršeni nalozi</span><strong>{result.totals.served}/{result.totals.orders}</strong></div>
        <div><span><Truck size={17} aria-hidden="true"/>Korišteni kamioni</span><strong>{result.totals.trucks_used} od {scenario.trucks.length}</strong></div>
      </section>
      <AlternativeStrip alternatives={result.analysis.alternatives} applySettings={applySettings} disabled={stale}/>
      {onDetailed && !result.analysis.alternatives.length && result.analysis.sensitivity.note.includes('na zahtjev') &&
        <button type="button" className="detail-button" disabled={stale} onClick={onDetailed}>Izračunaj drugo tumačenje</button>}
      {!result.totals.orders && <Callout>{hints.empty.orders}</Callout>}
    </>}
    {result?.messages.map((text,i)=><p className="plan-message" key={i}>{text}</p>)}
    {result && status !== 'INVALID_PLAN' && <Warnings unserved={result.unserved} onOrder={stale?undefined:onOrder}/>}
    {result && usable && <div className="truck-list">{result.trucks.map(truck=>
      <TruckCard key={truck.id} truck={truck} depot={scenario.depot} explanation={result.analysis.unused_trucks.find(u=>u.truck===truck.id)?.message}/>)}</div>}
  </div>
}
