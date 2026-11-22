import { api } from '../../api'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { formatKm } from '../../lib/format'
import { hasUsablePlan } from '../../lib/plan'
import type { Scenario, Settings, SolveResult, WhyRow } from '../../types'
import { ComparisonTable } from './ComparisonTable'
import { CurveChart } from './CurveChart'
import { useAnalysisRequest } from './useAnalysisRequest'
import './analysis.css'

interface Props {
  scenario: Scenario
  result: SolveResult
  applySettings: (patch: Partial<Settings>) => void
  onDetailed: () => void
  busy?: boolean
}

const number = new Intl.NumberFormat('hr-HR', {maximumFractionDigits: 4})
const minutes = (value: number) => number.format(value) + ' min'
const signed = (value: number, format: (v: number) => string) => (value > 0 ? '+' : value < 0 ? '−' : '') + format(Math.abs(value))

function WhyLine({scenario, result, applySettings, busy, row}: Omit<Props, 'onDetailed'> & {row: WhyRow}) {
  const request = useAnalysisRequest<SolveResult>(scenario, result)
  const pins = {...scenario.settings.pinned_orders, [row.order]: row.other_truck}
  const other = row.lazy ? request.value : null
  let message = row.impossible
  let km = row.lazy ? null : row.other_km
  let delta = row.lazy ? null : row.delta_km
  let objective = row.lazy ? null : row.delta_objective
  let group = row.lazy ? [] : row.other_truck_orders
  if (other) {
    if (!hasUsablePlan(other)) message = hints.status[other.validation.passed ? other.status : 'INVALID_PLAN'].title
    else if (other.solver !== 'exact' || other.optimality !== 'proven') message = 'Nema dokazanog optimuma za ovu raspodjelu.'
    else {
      const orders = other.trucks.find(truck => truck.id === row.other_truck)?.orders ?? []
      if (!orders.includes(row.order)) message = 'Nalog nije prevezen odabranim kamionom.'
      else {
        group = [...orders].sort()
        km = other.totals.km
        delta = Math.round((km - result.totals.km) * 10) / 10
        const end = (r: SolveResult) => Math.max(0, ...r.trucks.map(t => t.total_min))
        objective = Math.round((end(other) - end(result)) * 10) / 10
      }
    }
  }
  return <tr><th scope="row">{row.order}</th><td>{row.truck}</td><td>{row.other_truck}</td>
    <td>{message ?? (km !== null && <><strong>{formatKm(km)}</strong>
      {delta !== null && <span className="analysis-delta">{signed(delta,formatKm)}</span>}
      {result.settings.objective === 'makespan' && objective !== null &&
        <small>Promjena završetka {other && '≈ '}{signed(objective,minutes)}</small>}
      <small>Nalozi na {row.other_truck}: {group.join(', ')}</small>
      {other && other.totals.served !== result.totals.served && <small>Izvršeno {other.totals.served}/{other.totals.orders}</small>}
    </>)}{request.error && <span role="alert">{request.error}</span>}</td>
    <td>{!message && (km !== null ?
      <button type="button" className="analysis-action" disabled={busy}
        onClick={() => applySettings({pinned_orders:pins})}>Prikaži plan</button> :
      row.lazy && <button type="button" className="analysis-action" disabled={busy || request.waiting}
        onClick={() => request.run(signal => api.solve({...scenario, settings: {...scenario.settings, pinned_orders: pins}}, signal))}>
        {request.waiting ? 'Računam…' : 'Izračunaj'}</button>)}</td>
  </tr>
}

export function AnalysisView({scenario, result, applySettings, onDetailed, busy = false}: Props) {
  const {analysis} = result
  const sensitivity = analysis.sensitivity
  const usable = hasUsablePlan(result)
  const curveNote = analysis.binding.find(text => /krivulja/i.test(text))
  const bindings = analysis.binding.filter(text => text !== curveNote)
  const exact = usable && result.solver === 'exact' && result.optimality === 'proven'
  return <div className="analysis-view">
    <InfoLine>{hints.tabs.analysis}</InfoLine>
    {!usable && <p role="status">{hints.status[result.validation.passed ? result.status : 'INVALID_PLAN'].body}</p>}
    {bindings.length > 0 && <section className="analysis-card"><h3>Najtješnja ograničenja</h3>
      <ul>{bindings.map((text,i) => <li key={i}>{text}</li>)}</ul></section>}
    {exact && <div className="analysis-pair">
      <CurveChart points={analysis.curve} currentKm={result.totals.km} applySettings={applySettings}
        busy={busy} empty={curveNote ?? (!scenario.orders.length ? hints.empty.orders : 'Krivulja nije dostupna.')}/>
      <section className="analysis-card"><h3>Osjetljivost plana</h3>
        <dl className="analysis-stat-list">
          {sensitivity.limit_lower_min !== null && <div><dt>Najmanji limit za ovaj plan</dt><dd>{minutes(sensitivity.limit_lower_min)}</dd></div>}
          {sensitivity.better_plan_at_min !== null && <div><dt>Bolji plan dostupan od</dt><dd>{minutes(sensitivity.better_plan_at_min)}
            {sensitivity.better_plan_km !== null && ' · ' + formatKm(sensitivity.better_plan_km)}</dd></div>}
          {sensitivity.handling_max_min !== null && <div><dt>Najdulje trajanje radnje</dt><dd>{minutes(sensitivity.handling_max_min)}</dd></div>}
        </dl>
        {sensitivity.note && <p>{sensitivity.note}</p>}
        {sensitivity.note.includes('na zahtjev') && <button className="analysis-action" type="button" onClick={onDetailed}
          disabled={busy}>Izračunaj osjetljivost</button>}
      </section>
    </div>}
    {exact && analysis.why.length > 0 && <section className="analysis-card">
      <h3>Zašto ovakva raspodjela?</h3>
      <div className="analysis-table-scroll" tabIndex={0} role="region" aria-label="Raspodjela po nalozima">
        <table className="analysis-table" aria-label="Učinak premještanja naloga"><thead><tr>
          <th>Nalog</th><th>Kamion</th><th>Drugi kamion</th><th>Učinak premještanja</th><th>Raspored</th>
        </tr></thead><tbody>{analysis.why.map(row => <WhyLine key={JSON.stringify([row.order,row.other_truck])} row={row}
          scenario={scenario} result={result} applySettings={applySettings} busy={busy}/>)}</tbody></table>
      </div>
    </section>}
    {result.unserved.length > 0 && <section className="analysis-card"><h3>Neizvršeni nalozi</h3>
      <ul>{result.unserved.map(o => <li key={o.order}><strong>{o.order}</strong> · {o.message}</li>)}</ul></section>}
    <ComparisonTable scenario={scenario} busy={busy}/>
  </div>
}
