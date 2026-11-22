import { ArrowUpRight, TriangleAlert } from 'lucide-react'
import type { SolveResult } from '../../types'

export function Warnings({ unserved, onOrder }: { unserved:SolveResult['unserved']; onOrder?:(id:string)=>void }) {
  if (!unserved.length) return null
  return <section className="plan-warnings" aria-label="Neizvršeni nalozi">
    <h3><TriangleAlert size={17} aria-hidden="true"/>Neizvršeni nalozi</h3>
    <ul>{unserved.map(item=><li key={item.order}>
      {onOrder ? <button type="button" onClick={()=>onOrder(item.order)} aria-label={'Otvori nalog '+item.order}>
        {item.order}<ArrowUpRight size={14} aria-hidden="true"/>
      </button> : <strong>{item.order}</strong>}
      <code>{item.reason}</code><p>{item.message}</p>
    </li>)}</ul>
  </section>
}
