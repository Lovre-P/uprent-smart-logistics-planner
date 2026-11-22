import { api } from '../../api'
import { formatKm } from '../../lib/format'
import type { ComparisonRow, Scenario } from '../../types'
import { useAnalysisRequest } from './useAnalysisRequest'

export function ComparisonTable({scenario, busy = false}: {scenario: Scenario; busy?: boolean}) {
  const request = useAnalysisRequest<ComparisonRow[]>(scenario)
  return <section className="analysis-card">
    <div className="analysis-title"><h3>Usporedba scenarija</h3>
      {!request.value && <button type="button" className="analysis-action" disabled={busy || request.waiting}
        onClick={() => request.run(signal => api.compare(scenario, undefined, signal))}>Usporedi scenarije</button>}
    </div>
    {request.waiting && <p role="status">Računam usporedbu…</p>}
    {request.error && <p role="alert">{request.error}</p>}
    {request.value && <div className="analysis-table-scroll" tabIndex={0} role="region" aria-label="Rezultati usporedbe">
      <table className="analysis-table" aria-label="Usporedba scenarija"><thead><tr>
        <th>Scenarij</th><th>Udaljenost</th><th>Izvršeno</th><th>Kamioni</th><th>Valjana tumačenja</th>
      </tr></thead><tbody>{request.value.map(row => <tr key={row.label}>
        <th scope="row">{row.label}</th><td>{formatKm(row.km)}</td><td>{row.served}/{row.orders}</td>
        <td>{row.trucks_used}</td><td>{row.valid_under.length ? row.valid_under.join(' · ') : 'Nijedno'}</td>
      </tr>)}</tbody></table>
    </div>}
  </section>
}
