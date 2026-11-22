import type { ReactNode } from 'react'
import { CircleAlert, Info, OctagonAlert } from 'lucide-react'
export function Callout({ tone = 'info', children }: {
  tone?: 'info' | 'warning' | 'error'
  children: ReactNode
}) {
  const Icon = tone === 'info' ? Info : tone === 'warning' ? CircleAlert : OctagonAlert
  return <div className={'callout callout--' + tone} role={tone === 'error' ? 'alert' : undefined}>
    <Icon size={18} aria-hidden="true" /><div>{children}</div>
  </div>
}
