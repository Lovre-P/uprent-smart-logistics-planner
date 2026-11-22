import type { SolveResult } from '../types'

const plans = new Set(['OPTIMAL','OPTIMAL_PARTIAL','FEASIBLE','FEASIBLE_PARTIAL'])
export function hasUsablePlan(result: SolveResult): boolean {
  return result.validation.passed && plans.has(result.status)
}
const other = ['#81509d', '#167c70', '#a34561', '#526930', '#6575a9']
export function truckColor(id: string): string {
  if (id === 'A') return 'var(--truck-a)'
  if (id === 'B') return 'var(--truck-b)'
  const seed = [...id].reduce((hash, char) => (hash * 31 + char.charCodeAt(0)) >>> 0, 0)
  return other[seed % other.length]
}
