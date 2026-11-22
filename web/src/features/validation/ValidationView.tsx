import { Callout } from '../../components/Callout'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { formatDuration, formatKm } from '../../lib/format'
import { hasUsablePlan } from '../../lib/plan'
import type { SolveResult } from '../../types'
import '../plan/plan.css'

const labels:Record<string,string>={
  baza:'Povratak u bazu', kapacitet_kg:'Nosivost kamiona', mjesta:'Broj mjesta za strojeve',
  redoslijed:'Utovar prije istovara', isti_kamion:'Isti kamion za obje radnje',
  jednom:'Svaki nalog jednom', vrijeme:'Dnevni limit', km_dosljedno:'Dosljednost kilometraže',
  neizvrseni_dosljedno:'Popis neizvršenih naloga', svi_kamioni:'Korištenje svih kamiona',
}
function Comparison({result,comparison}:{result:SolveResult;comparison:SolveResult}) {
  if (!hasUsablePlan(comparison)) {
    const status = comparison.validation.passed ? comparison.status : 'INVALID_PLAN'
    return <Callout tone="warning">OR-Tools · {hints.status[status].title}. {hints.status[status].body}</Callout>
  }
  const finish=(r:SolveResult)=>Math.max(0,...r.trucks.map(t=>t.total_min))
  const agree=result.totals.km===comparison.totals.km && result.totals.served===comparison.totals.served &&
    (!result.settings.require_all_trucks || result.totals.trucks_used===comparison.totals.trucks_used) &&
    (result.settings.objective!=='makespan' || finish(result)===finish(comparison))
  return <>
    <p className="comparison-conclusion">{agree?'Rezultati se slažu za odabrani cilj.':'Solveri su pronašli različite rezultate.'}</p>
    <div className="comparison-scroll"><table className="solver-comparison"><thead><tr>
      {['Solver','Izvršeni nalozi','Kamioni','Udaljenost','Kraj radnog dana'].map(t=><th key={t} scope="col">{t}</th>)}
    </tr></thead><tbody>{[result,comparison].map((r,i)=><tr key={i}><th scope="row">{i?'OR-Tools':'Egzaktni'}</th>
      <td>{r.totals.served}/{r.totals.orders}</td><td>{r.totals.trucks_used}</td>
      <td>{formatKm(r.totals.km)}</td><td>{formatDuration(finish(r))}</td></tr>)}</tbody></table></div>
  </>
}
export function ValidationView({ result,comparison,comparing=false,comparisonError }: {
  result:SolveResult;comparison:SolveResult|null;comparing?:boolean;comparisonError?:string|null
}) {
  return <section className="validation-view">
    <InfoLine>{hints.tabs.validation}</InfoLine>
    {!hasUsablePlan(result) && <Callout tone={result.validation.passed?'warning':'error'}>
      {hints.status[result.validation.passed?result.status:'INVALID_PLAN'].body}
    </Callout>}
    <ul className="validation-list" aria-label="Provjerena pravila">
      {result.validation.checks.map(c=>{
        const tone=c.passed?'pass':c.severity==='info'?'note':'fail'
        return <li key={c.rule} className={'validation-'+tone}>
          <span className="check-symbol" aria-hidden="true">{c.passed?'✓':tone==='note'?'ⓘ':'×'}</span>
          <div><strong>{labels[c.rule] ?? c.rule}</strong><p>{c.detail}</p></div>
          <span className="check-outcome">{c.passed?'Prolazi':tone==='note'?'Napomena':'Ne prolazi'}</span>
        </li>
      })}
    </ul>
    {result.solver==='exact' && hasUsablePlan(result) && result.settings.compare_with_ortools && <section className="solver-panel" aria-label="Usporedba solvera">
      <h3>Usporedba solvera</h3>
      {comparing && <p role="status">OR-Tools računa usporedni plan…</p>}
      {comparisonError && <Callout tone="warning">{comparisonError}</Callout>}
      {comparison && <Comparison result={result} comparison={comparison}/>}
      {!comparing && !comparisonError && !comparison && <p>Usporedba još nije dostupna.</p>}
    </section>}
  </section>
}
