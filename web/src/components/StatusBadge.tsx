import { CheckCheck, CircleAlert, CircleCheck, OctagonAlert } from 'lucide-react'
import type { Optimality, PlanStatus } from '../types'
import { hints } from '../content/hints'

export function StatusBadge({ status, optimality }: { status: PlanStatus; optimality: Optimality }) {
  let display = status
  if (optimality !== 'proven' && (status === 'OPTIMAL' || status === 'OPTIMAL_PARTIAL')) {
    display = status === 'OPTIMAL' ? 'FEASIBLE' : 'FEASIBLE_PARTIAL'
  }
  const message = hints.status[display]
  const tone = display === 'INVALID_PLAN' ? 'error'
    : display === 'OPTIMAL' || display === 'FEASIBLE' ? 'success' : 'warning'
  const Icon = tone === 'error' ? OctagonAlert : tone === 'warning' ? CircleAlert
    : display === 'OPTIMAL' ? CheckCheck : CircleCheck
  return <span className={'status-badge status-badge--' + tone} title={message.body} tabIndex={0}>
    <Icon size={15} aria-hidden="true" />{message.title}<span className="sr-only">. {message.body}</span>
  </span>
}
