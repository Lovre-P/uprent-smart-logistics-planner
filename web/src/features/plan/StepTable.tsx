import type { TruckView } from '../../types'
import { formatKm, formatKg } from '../../lib/format'

const action = {PICKUP:'Utovar', DELIVERY:'Istovar', RETURN:'Povratak'}
export function StepTable({truck}:{truck:TruckView}) {
  return <div className="steps-scroll" tabIndex={0} role="region" aria-label={'Tablica koraka: '+truck.name}>
    <table className="steps-table" aria-label={'Koraci rute: '+truck.name}><thead><tr>
      {['Korak','Lokacija','Radnja','Nalog / stroj','Dionica','Ukupno','Dolazak – odlazak','Teret nakon radnje','Strojevi'].map(label=><th key={label} scope="col">{label}</th>)}
    </tr></thead><tbody>
      {truck.steps.map(step=><tr key={step.seq}><th scope="row">{step.seq}</th><td><b>{step.location}</b></td>
        <td><span className={'step-action step-action--'+step.action.toLowerCase()}>{action[step.action]}</span></td>
        <td>{step.order ?? '—'}{step.machine && <small>{step.machine}</small>}</td>
        <td>{formatKm(step.leg_km)}</td><td>{formatKm(step.cum_km)}</td>
        <td>{step.arrive} – {step.depart}</td><td>{formatKg(step.load_kg)}
          <meter aria-label={'Opterećenje nakon koraka '+step.seq} min={0} max={truck.capacity_kg} value={step.load_kg}/>
        </td>
        <td>{step.load_slots} / {truck.slots}{step.onboard.length>0 && <small>{step.onboard.join(', ')}</small>}</td>
      </tr>)}
    </tbody></table>
  </div>
}
