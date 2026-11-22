import { useId, useLayoutEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { ChevronDown, SlidersHorizontal } from 'lucide-react'
import { Hint } from '../../components/Hint'
import { hints } from '../../content/hints'
import { formatDuration } from '../../lib/format'
import { parseHrNumber } from '../../lib/parseNumber'
import { validateSetting } from '../../state/scenarioValidation'
import type { Settings } from '../../types'
import './settings.css'

interface Props { settings: Settings; onChange: (patch: Partial<Settings>) => void }
type NumericKey = 'day_limit_min'|'load_min'|'unload_min'|'exact_max_orders'|'exact_max_trucks'|'ortools_time_limit_s'

function SettingRow({ name, control, children, toggle = false }: {
  name:keyof Settings; control:string; children:ReactNode; toggle?:boolean
}) {
  return <div className={'setting-row' + (toggle ? ' setting-row--toggle' : '')} data-setting={name}>
    <div className="setting-label"><label htmlFor={control}>{hints.settings[name].title}</label><Hint id={name} /></div>
    {children}
  </div>
}
function NumberSetting({name, unit, settings, onChange}: Props & {name:NumericKey;unit?:string}) {
  const id = useId()
  const value = String(settings[name]).replace('.', ',')
  const [draft, setDraft] = useState(value)
  const [error, setError] = useState('')
  useLayoutEffect(() => { setDraft(value); setError('') }, [value])
  function commit() {
    try {
      const number = parseHrNumber(draft)
      validateSetting(name, number)
      setError('')
      if (number !== settings[name]) onChange({[name]:number})
    } catch (e) { setError((e as Error).message) }
  }
  return <SettingRow name={name} control={id}>
    <div className="setting-number"><input id={id} inputMode="decimal" value={draft}
      aria-invalid={!!error} aria-describedby={error ? id+'-error' : undefined}
      onChange={e=>setDraft(e.target.value)} onBlur={commit} onKeyDown={e=>{if(e.key==='Enter') e.currentTarget.blur()}} />
      <span>{unit}</span>{name === 'day_limit_min' && <strong>{formatDuration(settings.day_limit_min)}</strong>}
    </div>{error && <small id={id+'-error'} className="field-error" role="alert">{error}</small>}
  </SettingRow>
}
function Switch({name, settings, onChange}: Props & {name:'limit_includes_handling'|'allow_partial'|'require_all_trucks'|'compare_with_ortools'}) {
  const id = useId()
  return <SettingRow name={name} control={id} toggle>
    <input className="setting-switch" type="checkbox" role="switch" id={id} checked={settings[name]}
      onChange={e=>onChange({[name]:e.target.checked})} />
  </SettingRow>
}

export function SettingsPanel(props: Props) {
  const { settings, onChange } = props
  const id = useId()
  return <section className="settings-panel" aria-labelledby={id+'-settings'}>
    <h2 id={id+'-settings'}><SlidersHorizontal aria-hidden="true" size={18} />Postavke</h2>
    <NumberSetting name="day_limit_min" unit="min" {...props} />
    <Switch name="limit_includes_handling" {...props} />
    <NumberSetting name="load_min" unit="min" {...props} />
    <NumberSetting name="unload_min" unit="min" {...props} />
    <Switch name="require_all_trucks" {...props} />
    <Switch name="allow_partial" {...props} />
    <SettingRow name="objective" control={id+'-objective'}>
      <select id={id+'-objective'} value={settings.objective} onChange={e=>onChange({objective:e.target.value as Settings['objective']})}>
        <option value="km">Najmanje kilometara</option><option value="makespan">Najraniji završetak</option>
      </select>
    </SettingRow>
    <details className="advanced-settings"><summary>Napredno<ChevronDown size={15}/></summary>
      <SettingRow name="solver" control={id+'-solver'}>
        <select id={id+'-solver'} value={settings.solver} onChange={e=>onChange({solver:e.target.value as Settings['solver']})}>
          <option value="auto">Automatski</option><option value="exact">Egzaktni solver</option><option value="ortools">OR-Tools</option>
        </select>
      </SettingRow>
      <NumberSetting name="ortools_time_limit_s" unit="s" {...props} />
      <Switch name="compare_with_ortools" {...props} />
      <SettingRow name="day_start" control={id+'-time'}><input id={id+'-time'} type="time" value={settings.day_start}
        onChange={e=>{if(e.target.validity.valid && e.target.value) onChange({day_start:e.target.value})}} /></SettingRow>
      <NumberSetting name="exact_max_orders" {...props} />
      <NumberSetting name="exact_max_trucks" {...props} />
      {Object.keys(settings.pinned_orders ?? {}).length > 0 && <SettingRow name="pinned_orders" control={id+'-pins'}>
        <p>{Object.entries(settings.pinned_orders ?? {}).map(([order,truck])=>order+' → '+truck).join(', ')}</p>
        <button id={id+'-pins'} type="button" onClick={()=>onChange({pinned_orders:{}})}>Ukloni prikvačene naloge</button>
      </SettingRow>}
    </details>
  </section>
}
