import { GitBranch, ArrowRight } from 'lucide-react'
import type { Alternative, Settings } from '../../types'
import { formatKm } from '../../lib/format'

function reading(row:Alternative) {
  if (row.setting==='limit_includes_handling') return row.value ? 'U limit ulaze vožnja, utovar i istovar' : 'U limit ulazi samo vožnja'
  return row.value ? 'Svaki kamion mora voziti' : 'Kamion može ostati u bazi'
}
export function AlternativeStrip({alternatives,applySettings,disabled=false}:{
  alternatives:Alternative[];applySettings:(patch:Partial<Settings>)=>void;disabled?:boolean
}) {
  if (!alternatives.length) return null
  return <section className="alternative-strip" aria-label="Drugo tumačenje">
    <h3><GitBranch size={16} aria-hidden="true"/>Drugo tumačenje</h3>
    {alternatives.map((row,index)=><div className="alternative-row" key={row.setting}>
      <p>{reading(row)} <span className="alternative-metric">→ {formatKm(row.km)}.</span>
        <span className="alternative-detail"> {row.summary} Izvršeno {row.served} naloga.</span></p>
      <button type="button" disabled={disabled} aria-label={index ? 'Primijeni: '+reading(row):'Primijeni'}
        onClick={()=>applySettings({[row.setting]:row.value})}>Primijeni<ArrowRight size={14} aria-hidden="true"/></button>
    </div>)}
  </section>
}
