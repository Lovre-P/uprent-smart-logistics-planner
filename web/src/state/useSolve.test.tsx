import { act, render, renderHook, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import data from '../../../data/default_scenario.json'
import normal from '../test/fixtures/default-result.json'
import strict from '../test/fixtures/strict-result.json'
import type { Scenario } from '../types'
import { useSolve } from './useSolve'
import { PlanView } from '../features/plan/PlanView'

const scenario = {...data,settings:{...data.settings,compare_with_ortools:false}} as Scenario
function queue() {
  const requests: { body:{scenario:Scenario}; signal:AbortSignal; reply:(json:unknown)=>void; fail:()=>void }[]=[]
  vi.stubGlobal('fetch', vi.fn((_url,init) => new Promise<Response>((resolve,reject) => {
    requests.push({body:JSON.parse(init.body),signal:init.signal,
      reply:json=>resolve(Response.json(json)),fail:()=>reject(new Error('Mrežna greška'))})
  })))
  return requests
}
const waitDebounce=()=>act(async()=>{await vi.advanceTimersByTimeAsync(300)})
beforeEach(()=>vi.useFakeTimers())
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals()})
it('ignorira stariji odgovor i otkazuje prethodni zahtjev', async () => {
  const requests=queue()
  const {result,rerender}=renderHook(({s})=>useSolve(s),{initialProps:{s:scenario}})
  await waitDebounce()
  rerender({s:{...scenario,settings:{...scenario.settings,limit_includes_handling:true}}})
  expect(requests[0].signal.aborted).toBe(true)
  await waitDebounce()
  await act(async()=>requests[1].reply(strict))
  await act(async()=>requests[0].reply(normal))
  expect(result.current.result?.totals.km).toBe(200.1)
})
it('odmah prikazuje rezultat i zasebno računa usporedbu samo za pripadajući scenarij', async () => {
  const requests=queue()
  const compared={...scenario,settings:{...scenario.settings,compare_with_ortools:true}}
  const {result,rerender}=renderHook(({s})=>useSolve(s),{initialProps:{s:compared as Scenario}})
  await waitDebounce()
  await act(async()=>requests[0].reply(normal))
  expect(result.current.result?.totals.km).toBe(182.2)
  expect(result.current.computing).toBe(false)
  expect(result.current.comparing).toBe(true)
  expect(requests[1].body.scenario.settings.solver).toBe('ortools')
  rerender({s:scenario})
  await waitDebounce()
  await act(async()=>requests[2].reply(strict))
  await act(async()=>requests[1].reply({...normal,solver:'ortools'}))
  expect(result.current.comparison).toBeNull()
  expect(requests[1].signal.aborted).toBe(true)
})
it('tijekom novog izračuna i nakon mrežne greške ostavlja prethodni plan', async () => {
  const requests=queue()
  function Page({s}:{s:Scenario}) {
    const state=useSolve(s)
    return <PlanView result={state.result} scenario={state.resultScenario ?? s} applySettings={()=>{}}
      computing={state.computing} error={state.error}/>
  }
  const {rerender}=render(<Page s={scenario}/>)
  await waitDebounce()
  await act(async()=>requests[0].reply(normal))
  rerender(<Page s={{...scenario,name:'Novi scenarij'}}/>)
  expect(screen.getByText('Računam…')).toBeTruthy()
  expect(screen.getByRole('region',{name:'Sažetak plana'}).textContent).toContain('182,2 km')
  await waitDebounce()
  await act(async()=>requests[1].fail())
  expect(screen.getByRole('alert').textContent).toContain('Poslužitelj')
  expect(screen.getByRole('region',{name:'Sažetak plana'}).textContent).toContain('182,2 km')
})
