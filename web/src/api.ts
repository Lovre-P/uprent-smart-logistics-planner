import type { ComparisonRow, Plan, Preset, Scenario, SolveResult, ValidationReport } from './types'

const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

async function request<T>(path: string, signal?: AbortSignal, payload?: unknown): Promise<T> {
  const init: RequestInit = { signal, headers: { Accept: 'application/json' } }
  if (payload !== undefined) {
    init.method = 'POST'
    init.headers = { ...init.headers, 'Content-Type': 'application/json' }
    init.body = JSON.stringify(payload)
  }
  let response: Response
  try {
    response = await fetch(base + '/api/' + path, init)
  } catch (error) {
    if (signal?.aborted) throw error
    throw new Error('Poslužitelj nije dostupan. Provjerite vezu i pokušajte ponovno.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(typeof body?.detail === 'string' ? body.detail : 'Zahtjev nije uspio (' + response.status + ').')
  }
  return response.json() as Promise<T>
}

export const api = {
  health: (signal?: AbortSignal) => request<{status: string}>('health', signal),
  defaultScenario: (signal?: AbortSignal) => request<Scenario>('scenario/default', signal),
  solve: (scenario: Scenario, signal?: AbortSignal) => request<SolveResult>('solve', signal, { scenario }),
  validate: (scenario: Scenario, plan: Plan, signal?: AbortSignal) =>
    request<ValidationReport>('validate', signal, { scenario, plan }),
  compare: (scenario: Scenario, variants?: Preset[], signal?: AbortSignal) =>
    request<ComparisonRow[]>('compare', signal, { scenario, variants }),
}
