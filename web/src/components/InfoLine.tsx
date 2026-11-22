import type { ReactNode } from 'react'
export function InfoLine({children}: {children: ReactNode}) {
  return <p className="info-line">{children}</p>
}
