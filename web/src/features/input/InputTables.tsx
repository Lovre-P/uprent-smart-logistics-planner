import { Fragment, useId, useRef, useState } from 'react'
import { Download, FileUp, Pencil, Plus, RotateCcw, Trash2 } from 'lucide-react'
import { api } from '../../api'
import { InfoLine } from '../../components/InfoLine'
import { hints } from '../../content/hints'
import { parseHrNumber } from '../../lib/parseNumber'
import { groups, InputError, readScenario } from '../../state/scenarioValidation'
import type { Group } from '../../state/scenarioValidation'
import type { Scenario } from '../../types'
import './input.css'

interface Props {
  scenario: Scenario
  onChange: (scenario: Scenario) => void
  onReset?: () => void
  focusOrder?: string | null
}
interface Draft { group: Group; index: number | null; fields: Record<string, string> }
interface Notice { group?: Group; field?: string; message: string }
const groupKeys = Object.keys(groups) as Group[]
const decimal = new Intl.NumberFormat('hr-HR', {maximumFractionDigits: 12, useGrouping:'always'})

function nextId(group: Group, scenario: Scenario) {
  const ids = new Set(scenario[group].map(row => row.id))
  if (group === 'trucks') {
    for (let i = 0; i < 26; i++) if (!ids.has(String.fromCharCode(65+i))) return String.fromCharCode(65+i)
  }
  const prefix = {locations:'L', machines:'M', trucks:'K', orders:'N'}[group]
  const width = group === 'machines' || group === 'orders' ? 2 : 1
  let n = 1
  while (ids.has(prefix + String(n).padStart(width,'0'))) n++
  return prefix + String(n).padStart(width,'0')
}

function makeDraft(group: Group, index: number | null, scenario: Scenario): Draft {
  const row = index === null ? undefined : scenario[group][index]
  const availableMachine = scenario.machines.find(m => !scenario.orders.some(o=>o.machine === m.id))
  const defaults: Record<string, string> = {
    id:nextId(group,scenario), name:'', x:'0', y:'0', weight_kg:'', capacity_kg:'', slots:'1', speed_kmh:'60',
    machine:availableMachine?.id ?? '', pickup:scenario.depot,
    delivery:scenario.locations.find(l=>l.id !== scenario.depot)?.id ?? '', load_min:'', unload_min:'',
  }
  const fields: Record<string,string> = {}
  for (const col of groups[group].columns) {
    const val = row ? (row as unknown as Record<string,unknown>)[col.key] : defaults[col.key]
    fields[col.key] = val == null ? '' : String(val)
    if (col.type === 'number') fields[col.key] = fields[col.key].replace('.', ',')
  }
  return {group, index, fields}
}

function applyRename(s: Scenario, group: Group, oldId: string, id: string) {
  if (oldId === id) return
  if (group === 'locations') {
    if (s.depot === oldId) s.depot = id
    for (const o of s.orders) {
      if (o.pickup === oldId) o.pickup = id
      if (o.delivery === oldId) o.delivery = id
    }
  }
  if (group === 'machines') for (const o of s.orders) { if (o.machine === oldId) o.machine = id }
  const pins = s.settings.pinned_orders
  if (pins && group === 'orders' && Object.hasOwn(pins, oldId)) {
    s.settings.pinned_orders = Object.fromEntries(Object.entries(pins).map(([o,t])=>[o === oldId ? id : o,t]))
  }
  if (pins && group === 'trucks') {
    for (const [o,t] of Object.entries(pins)) if (t===oldId) pins[o]=id
  }
}

export function InputTables({scenario, onChange, onReset, focusOrder}: Props) {
  const uid = useId()
  const upload = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [notice,setNotice] = useState<Notice | null>(null)
  function report(error: unknown, group?: Group) {
    setNotice({group,field:error instanceof InputError ? error.field : undefined,
      message:error instanceof Error ? error.message : 'Provjerite unesene podatke.'})
  }
  function accept(raw: unknown) {
    const valid = readScenario(raw)
    onChange(valid)
    setNotice(null)
    setDraft(null)
  }
  function start(group: Group, index: number | null) {
    const next = makeDraft(group, index, scenario)
    if (group === 'orders' && index === null && !next.fields.machine) {
      setDraft(null)
      setNotice({ group, message: hints.empty.availableMachines })
      return
    }
    setNotice(null)
    setDraft(next)
  }
  function save() {
    if (!draft) return
    try {
      const {group,index,fields} = draft
      const row: Record<string, unknown> = {}
      for (const col of groups[group].columns) {
        const v = fields[col.key].trim()
        if (col.optional && !v) continue
        row[col.key] = col.type === 'number' ? parseHrNumber(v) : v
        if (row[col.key] === null) throw new InputError(col.key, 'Unesite broj za polje ' + col.title + '.')
      }
      const s = structuredClone(scenario)
      if (index !== null) applyRename(s,group,s[group][index].id,fields.id.trim())
      const rows: unknown[] = [...s[group]]
      if (index === null) rows.push(row)
      else rows[index] = row
      accept({...s,[group]:rows})
    } catch (e) { report(e,draft.group) }
  }
  function remove(group:Group,index:number) {
    try { accept({...scenario, [group]:scenario[group].filter((_,i)=>i!==index)}) }
    catch (e) { report(e,group) }
  }
  async function importFile(file?: File) {
    if (!file) return
    try {
      const text = await new Promise<string>((resolve,reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(String(reader.result))
        reader.onerror = () => reject(new Error('Čitanje datoteke nije uspjelo.'))
        reader.readAsText(file)
      })
      let raw: unknown
      try { raw = JSON.parse(text.replace(/^\uFEFF/,'')) } catch { throw new Error('Datoteka ne sadrži valjan JSON.') }
      accept(raw)
    } catch (e) { report(e) }
    finally { if (upload.current) upload.current.value='' }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(scenario,null,2)],{type:'application/json'}))
    const a = document.createElement('a')
    a.href = url; a.download = 'uprent-scenarij.json'; a.click()
    window.setTimeout(()=>URL.revokeObjectURL(url),1000)
  }
  async function reset() {
    try {
      if (onReset) { onReset(); setDraft(null); setNotice(null) }
      else accept(await api.defaultScenario())
    } catch (e) { report(e) }
  }

  function editor() {
    if (!draft) return null
    const { group,fields } = draft
    return <form className="row-editor" aria-label={'Uređivanje: '+groups[group].title}
      onSubmit={e=>{e.preventDefault();save()}}>
      {groups[group].columns.map(col => {
        const fieldId = uid+'-field-'+col.key
        const fieldError = notice?.group === group && notice.field === col.key ? notice.message : null
        return <div key={col.key}><label htmlFor={fieldId}>{col.title}</label>
          <input id={fieldId} autoFocus={col.key==='id'} value={fields[col.key]}
            inputMode={col.type === 'number'?'decimal':undefined} list={col.list?uid+'-choices-'+col.list:undefined}
            aria-invalid={!!fieldError} aria-describedby={fieldError ? fieldId+'-error' : undefined}
            onChange={e=>{setDraft({...draft,fields:{...fields,[col.key]:e.target.value}}); setNotice(null)}}/>
          {fieldError && <small id={fieldId+'-error'} role="alert" className="field-error">{fieldError}</small>}
        </div>
      })}
      <div className="row-editor-actions">
        <button type="submit" className="solid-button">Spremi {groups[group].noun}</button>
        <button type="button" onClick={()=>{setDraft(null);setNotice(null)}}>Odustani</button>
      </div>
    </form>
  }

  return <div className="input-tables">
    <InfoLine>{hints.tabs.input}</InfoLine>
    <div className="data-actions">
      <button type="button" onClick={()=>upload.current?.click()}><FileUp size={16}/>Uvezi JSON</button>
      <input hidden ref={upload} type="file" accept=".json,application/json" aria-label="Uvezi JSON"
        onChange={e=>void importFile(e.target.files?.[0])} />
      <button type="button" onClick={download}><Download size={16}/>Izvezi JSON</button>
      <button type="button" onClick={()=>void reset()}><RotateCcw size={15}/>Vrati podatke iz zadatka</button>
    </div>
    {notice && !notice.group && <p className="field-error" role="alert">{notice.message}</p>}
    {groupKeys.map(group => {
      const {title,noun,columns} = groups[group]
      const d = draft?.group===group ? draft : null
      const inField = d && notice?.field && columns.some(c=>c.key===notice.field)
      return <section className="data-section" key={group} aria-labelledby={uid+'-title-'+group}>
        <div className="data-section-heading"><h3 id={uid+'-title-'+group}>{title}</h3>
          <button type="button" onClick={()=>start(group,null)}><Plus size={15}/>Dodaj {noun}</button>
        </div>
        {notice?.group===group && !inField && <p className="field-error" role="alert">{notice.message}</p>}
        {d && d.index === null && editor()}
        <div className="data-scroll"><table aria-label={title}><thead><tr>
          {columns.map(col=><th key={col.key} scope="col">{col.title}</th>)}<th scope="col"><span className="sr-only">Uređivanje</span></th>
        </tr></thead><tbody>
          {scenario[group].map((row,index)=><Fragment key={row.id}>
            <tr id={group==='orders'?'order-'+encodeURIComponent(row.id):undefined} tabIndex={-1}
              className={group==='orders' && focusOrder === row.id?'focused-order':undefined}>
              {columns.map(col=>{
                const val = (row as unknown as Record<string, unknown>)[col.key]
                const value = typeof val === 'number' ? decimal.format(val) : String(val ?? '—')
                return col.key==='id' ? <th key={col.key} scope="row">{value}</th> : <td key={col.key}>{value}</td>
              })}
              <td><div className="row-actions"><button type="button" aria-label={'Uredi '+row.id}
                title={'Uredi '+row.id} onClick={()=>start(group,index)}><Pencil size={14}/></button>
                <button type="button" aria-label={'Obriši '+row.id} title={'Obriši '+row.id}
                  onClick={()=>remove(group,index)}><Trash2 size={14}/></button></div></td>
            </tr>
            {d?.index === index && <tr><td colSpan={columns.length+1}>{editor()}</td></tr>}
          </Fragment>)}
        </tbody></table></div>
        {!scenario[group].length && <p className="empty-table">{group==='orders'?hints.empty.orders:'Nema stavki.'}</p>}
      </section>
    })}
    {(['locations','machines'] as const).map(g=><datalist id={uid+'-choices-'+g} key={g}>
      {scenario[g].map(x=><option key={x.id} value={x.id}/>)}</datalist>)}
  </div>
}
