export interface Location { id: string; name?: string | null; x: number; y: number }
export interface Machine { id: string; weight_kg: number }
export interface Truck { id: string; name?: string | null; capacity_kg: number; slots: number; speed_kmh: number }
export interface Order {
  id: string
  machine: string
  pickup: string
  delivery: string
  load_min?: number | null
  unload_min?: number | null
}

export interface Settings {
  day_limit_min: number
  limit_includes_handling: boolean
  load_min: number
  unload_min: number
  require_all_trucks: boolean
  allow_partial: boolean
  objective: 'km' | 'makespan'
  solver: 'auto' | 'exact' | 'ortools'
  ortools_time_limit_s: number
  compare_with_ortools: boolean
  day_start: string
  exact_max_orders: number
  exact_max_trucks: number
  pinned_orders?: Record<string, string> | null
}
export const SETTINGS_KEYS = [
  'day_limit_min', 'limit_includes_handling', 'load_min', 'unload_min', 'require_all_trucks',
  'allow_partial', 'objective', 'solver', 'ortools_time_limit_s', 'compare_with_ortools',
  'day_start', 'exact_max_orders', 'exact_max_trucks', 'pinned_orders',
] as const satisfies readonly (keyof Settings)[]

export interface Scenario {
  name: string
  depot: string
  locations: Location[]
  machines: Machine[]
  trucks: Truck[]
  orders: Order[]
  settings: Settings
}

export type PlanStatus = 'OPTIMAL' | 'OPTIMAL_PARTIAL' | 'FEASIBLE' | 'FEASIBLE_PARTIAL'
  | 'NO_FULL_PLAN' | 'NOT_FOUND' | 'INVALID_PLAN'
export type Optimality = 'proven' | 'best_found' | 'none'
export type LimitBasis = 'drive' | 'drive+handling'
export type Operation = 'PICKUP' | 'DELIVERY'
export interface Plan {
  routes: Record<string, [Operation, string][]>
  reported_km?: Record<string, number> | null
  reported_unserved?: string[] | null
}
export interface StepView {
  seq: number
  location: string
  action: Operation | 'RETURN'
  order: string | null
  machine: string | null
  leg_km: number
  cum_km: number
  arrive: string
  depart: string
  load_kg: number
  load_slots: number
  onboard: string[]
}
export interface TruckView {
  id: string
  name: string
  used: boolean
  km: number
  drive_min: number
  handling_min: number
  total_min: number
  limit_min: number
  limit_basis: LimitBasis
  slack_min: number
  peak_kg: number
  capacity_kg: number
  peak_slots: number
  slots: number
  orders: string[]
  steps: StepView[]
}
export interface Check { rule: string; passed: boolean; detail: string; severity: 'hard' | 'info' }
export interface ValidationReport {
  passed: boolean
  checks: Check[]
  trucks: TruckView[]
  total_km: number
  served: string[]
  unserved: string[]
}
export interface WhyRow {
  order: string
  truck: string
  other_truck: string
  other_km: number | null
  delta_km: number | null
  delta_objective: number | null
  other_truck_orders: string[]
  impossible: string | null
  lazy: boolean
}
export interface Sensitivity {
  limit_basis: LimitBasis
  limit_lower_min: number | null
  better_plan_at_min: number | null
  better_plan_km: number | null
  handling_max_min: number | null
  next_plan_km: number | null
  note: string
}
export interface Alternative {
  setting: 'limit_includes_handling' | 'require_all_trucks'
  value: boolean
  km: number
  served: number
  trucks_used: number
  summary: string
}
export interface Analysis {
  why: WhyRow[]
  unused_trucks: { truck: string; message: string }[]
  alternatives: Alternative[]
  binding: string[]
  sensitivity: Sensitivity
  curve: { km: number; end_min: number; by_truck: Record<string, string[]> }[]
}
export type ReasonCode = 'TOO_HEAVY' | 'TOO_LONG_ALONE' | 'DOES_NOT_FIT_TOGETHER' | 'NOT_FOUND'
export interface SolveResult {
  status: PlanStatus
  optimality: Optimality
  solver: 'exact' | 'ortools'
  settings: Settings
  totals: { km: number; served: number; orders: number; trucks_used: number }
  trucks: TruckView[]
  unserved: { order: string; reason: ReasonCode; message: string }[]
  validation: Pick<ValidationReport, 'passed' | 'checks'>
  analysis: Analysis
  comparison: null
  messages: string[]
  timings_ms: Record<string, number>
}
export interface ComparisonRow {
  label: string
  km: number
  served: number
  orders: number
  trucks_used: number
  valid_under: string[]
}
export interface Preset {
  label: string
  overrides: Partial<Settings>
  truck_overrides?: Partial<Truck> | null
}
