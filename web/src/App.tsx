import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'
import {
  ChartNoAxesCombined, ClipboardList, Clock3, Forklift, ListChecks, Map,
  PanelLeftOpen, RotateCcw, Route, SlidersHorizontal, Table2, X,
} from 'lucide-react'
import { Callout } from './components/Callout'
import { StatusBadge } from './components/StatusBadge'
import { hints } from './content/hints'
import { AnalysisView } from './features/analysis/AnalysisView'
import { InputTables } from './features/input/InputTables'
import { MapView } from './features/map/MapView'
import { PlanView } from './features/plan/PlanView'
import { SettingsPanel } from './features/settings/SettingsPanel'
import { TimelineView } from './features/timeline/TimelineView'
import { ValidationView } from './features/validation/ValidationView'
import { hasUsablePlan } from './lib/plan'
import { useScenario } from './state/useScenario'
import { useSolve } from './state/useSolve'
import type { Settings } from './types'
import './app.css'

const tabs = [
  {id:'plan',label:'Plan',heading:'Plan prijevoza',Icon:ClipboardList},
  {id:'map',label:'Karta',heading:'Karta ruta',Icon:Map},
  {id:'timeline',label:'Vremenska crta',heading:'Vremenska crta',Icon:Clock3},
  {id:'analysis',label:'Analiza',heading:'Analiza rasporeda',Icon:ChartNoAxesCombined},
  {id:'validation',label:'Provjera',heading:'Provjera plana',Icon:ListChecks},
  {id:'input',label:'Ulazni podaci',heading:'Ulazni podaci',Icon:Table2},
] as const
type Tab = typeof tabs[number]['id']
const storageKey = 'uprent.firstSteps.closed'

function Help({onSelect, onSteps, onReset}:{onSelect:(tab:Tab)=>void;onSteps:()=>void;onReset:()=>void}) {
  const [open,setOpen]=useState(false)
  const host=useRef<HTMLDivElement>(null)
  const button=useRef<HTMLButtonElement>(null)
  useEffect(()=>{
    if (!open) return
    const outside=(e:PointerEvent)=>{ if(e.target instanceof Node && !host.current?.contains(e.target)) setOpen(false) }
    const escape=(e:globalThis.KeyboardEvent)=>{if(e.key==='Escape'){setOpen(false);button.current?.focus()}}
    document.addEventListener('pointerdown',outside)
    document.addEventListener('keydown',escape)
    return ()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape)}
  },[open])
  function choose(fn:()=>void){setOpen(false);fn();button.current?.focus()}
  return <div className="help-control" ref={host}>
    <button ref={button} className="help-button" type="button" aria-label="Pomoć" aria-expanded={open}
      aria-controls={open?'help-panel':undefined} onClick={()=>setOpen(v=>!v)}>?</button>
    {open && <section id="help-panel" className="help-panel" aria-label="Pomoć">
      <h2>Pomoć</h2>
      <ul>{tabs.map(({id,label})=><li key={id}><button onClick={()=>choose(()=>onSelect(id))}>
        <strong>{label}</strong><span>{hints.tabs[id]}</span>
      </button></li>)}</ul>
      <button className="help-action" onClick={()=>choose(onSteps)}><PanelLeftOpen size={15}/>Prikaži prve korake</button>
      <button className="help-action" onClick={()=>choose(onReset)}><RotateCcw size={15}/>Vrati podatke i postavke iz zadatka</button>
    </section>}
  </div>
}

function SettingsDrawer({children,onClose}:{children:ReactNode;onClose:()=>void}) {
  const drawerRef=useRef<HTMLElement>(null)
  useEffect(()=>{drawerRef.current?.querySelector('button')?.focus()},[])
  function key(event:KeyboardEvent) {
    if(event.key==='Escape'){
      if (document.querySelector('[role="tooltip"]')) return
      event.preventDefault()
      onClose()
    } else if(event.key==='Tab'){
      const elements=[...(drawerRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input,select,summary,[tabindex="0"]')??[])]
        .filter(el=>!el.closest('details:not([open])') || el.matches('summary'))
      const first=elements[0],last=elements.at(-1)
      if (event.shiftKey && document.activeElement===first){event.preventDefault();last?.focus()}
      else if (!event.shiftKey && document.activeElement===last){event.preventDefault();first?.focus()}
    }
  }
  return <div className="drawer-layer" onMouseDown={e=>{if(e.target===e.currentTarget)onClose()}}>
    <section ref={drawerRef} role="dialog" aria-modal="true" aria-label="Postavke" id="settings-drawer"
      className="settings-drawer" onKeyDown={key}>
      <button className="drawer-close" onClick={onClose} aria-label="Zatvori postavke"><X size={19}/></button>
      {children}
    </section>
  </div>
}

export default function App() {
  const setup=useScenario()
  const {scenario,formRevision}=setup
  const solve=useSolve(scenario)
  const {result,resultScenario,computing,error}=solve
  const [tab,setTab]=useState<Tab>('plan')
  const [showSteps,setShowSteps]=useState(()=>{try{return localStorage.getItem(storageKey)!=='1'}catch{return true}})
  const [narrow,setNarrow]=useState(()=>window.innerWidth<=800)
  const [drawer,setDrawer]=useState(false)
  const [focusOrder,setFocusOrder]=useState<string|null>(null)
  const openDrawerButton=useRef<HTMLButtonElement>(null)
  const shell=useRef<HTMLDivElement>(null)
  const active=tabs.find(t=>t.id===tab)!
  const busy=computing || !!error
  const usable=result && hasUsablePlan(result)
  const status=result && (result.validation.passed?result.status:'INVALID_PLAN')
  function choose(id:Tab) {setFocusOrder(null);setTab(id)}
  function switchToPlan(patch:Partial<Settings>) {setup.applySettings(patch);choose('plan')}
  function reset(){setup.resetToTask();choose('plan')}
  function firstSteps(visible:boolean) {
    setShowSteps(visible)
    try{if (visible) localStorage.removeItem(storageKey);else localStorage.setItem(storageKey,'1')}catch{/* Privremena pohrana u ovoj kartici. */}
  }
  useEffect(()=>{
    const resize=()=>{setNarrow(window.innerWidth<=800);if(window.innerWidth>800)setDrawer(false)}
    window.addEventListener('resize',resize)
    return ()=>window.removeEventListener('resize',resize)
  },[])
  useEffect(()=>{
    if(tab!=='input'||!focusOrder)return
    const row=document.getElementById('order-'+encodeURIComponent(focusOrder))
    row?.focus({preventScroll:true})
    row?.scrollIntoView?.({block:'center'})
  },[tab,focusOrder])
  useEffect(()=>{
    if (shell.current) shell.current.inert=drawer && narrow
  },[drawer,narrow])

  function dismissDrawer(){
    setDrawer(false)
    if(shell.current)shell.current.inert=false
    openDrawerButton.current?.focus()
  }
  function tabKeys(e:KeyboardEvent<HTMLButtonElement>, index:number) {
    const next=e.key==='ArrowRight'?(index+1)%tabs.length:
      e.key==='ArrowLeft'?(index+tabs.length-1)%tabs.length:e.key==='Home'?0:e.key==='End'?tabs.length-1:null
    if(next===null)return
    e.preventDefault();choose(tabs[next].id);document.getElementById('tab-'+tabs[next].id)?.focus()
  }
  function panel() {
    if(!scenario)return setup.error?null:<p role="status">Učitavam podatke…</p>
    if(tab==='input')return <InputTables key={formRevision} scenario={scenario} onChange={setup.setScenario}
      onReset={reset} focusOrder={focusOrder}/>
    const viewScenario=resultScenario??scenario
    if(tab==='plan')return <PlanView scenario={viewScenario} result={result} applySettings={switchToPlan}
      onOrder={id=>{setTab('input');setFocusOrder(id)}} onDetailed={()=>solve.recalculate(true)} computing={computing} error={error}/>
    if(!result)return null
    if(tab==='validation')return <ValidationView result={result} comparison={solve.comparison}
      comparing={solve.comparing} comparisonError={solve.comparisonError}/>
    if(!usable && status)return <Callout tone={status==='INVALID_PLAN'?'error':'warning'}>
      <strong>{hints.status[status].title}</strong><p>{hints.status[status].body}</p>
    </Callout>
    if(tab==='map')return <MapView scenario={viewScenario} result={result}/>
    if(tab==='timeline')return <TimelineView scenario={viewScenario} result={result}/>
    return <AnalysisView scenario={viewScenario} result={result} applySettings={switchToPlan}
      onDetailed={()=>solve.recalculate(true)} busy={busy}/>
  }
  const settingsPanel=scenario && <SettingsPanel key={formRevision} settings={scenario.settings} onChange={setup.applySettings}/>
  return <>
    <div className="planner-shell" ref={shell}>
      <header className="planner-header"><div className="header-inner">
        <div className="product-name" aria-label="UP RENT Smart Logistics Planner">
          <span className="product-mark"><Forklift size={27} strokeWidth={1.9} aria-hidden="true"/></span>
          <h1><b>UP RENT</b><span>Smart Logistics Planner</span></h1>
        </div>
        <div className="header-tools">
          {result&&status&&<span className="header-status">
            {busy && <small>Prethodni plan</small>}<StatusBadge status={status} optimality={result.optimality}/>
          </span>}
          <button className="solve-button" type="button" onClick={()=>solve.recalculate()} disabled={!scenario||computing}>
            <Route size={17} aria-hidden="true"/>Izračunaj plan</button>
          <Help onSelect={choose} onSteps={()=>firstSteps(true)} onReset={reset}/>
        </div>
      </div></header>
      <main className="workspace">
        {!narrow && <aside className="settings-aside" aria-label="Postavke">{settingsPanel}</aside>}
        <div className="workspace-main">
          {showSteps && <section className="first-steps" aria-label="Prvi koraci">
            <strong>Prvi koraci</strong><ol>{hints.firstSteps.map((step,i)=>
              <li key={step}><span aria-hidden="true">{i+1}</span>{step}</li>)}</ol>
            <button onClick={()=>firstSteps(false)} aria-label="Zatvori prve korake"><X size={16}/></button>
          </section>}
          {narrow && <button ref={openDrawerButton} className="drawer-trigger" aria-expanded={drawer} aria-controls="settings-drawer"
            disabled={!scenario} onClick={()=>setDrawer(true)}><SlidersHorizontal size={16}/>Postavke</button>}
          <nav className="view-tabs" role="tablist" aria-label="Prikaz planera">
            {tabs.map(({id,label,Icon},i)=><button role="tab" key={id} id={'tab-'+id} aria-controls={'panel-'+id}
              aria-selected={tab===id} tabIndex={tab===id?0:-1} onKeyDown={e=>tabKeys(e,i)} onClick={()=>choose(id)}>
              <Icon size={16} strokeWidth={1.7} aria-hidden="true"/>{label}
            </button>)}
          </nav>
          {setup.error && <Callout tone="error">{setup.error}</Callout>}
          {tabs.map(({id})=><section key={id} hidden={id!==tab} id={'panel-'+id} role="tabpanel" aria-labelledby={'tab-'+id} tabIndex={0}>
            {id===tab && <>
              <div className="view-heading"><h2>{active.heading}</h2></div>
              {id!=='plan'&&computing&&<p className="view-working" role="status">Računam…{result && ' Prikazan je prethodni plan.'}</p>}
              {id!=='plan'&&error&&<Callout tone="error">{error}{result && ' Prikazan je posljednji uspješan izračun.'}</Callout>}
              {panel()}
            </>}
          </section>)}
        </div>
      </main>
    </div>
    {narrow && drawer && <SettingsDrawer onClose={dismissDrawer}>{settingsPanel}</SettingsDrawer>}
  </>
}
