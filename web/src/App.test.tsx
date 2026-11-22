import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import App from './App'
import { api } from './api'
import type { Scenario, SolveResult } from './types'
import data from '../../data/default_scenario.json'
import normal from './test/fixtures/default-result.json'
import heavy from './test/fixtures/n11-result.json'

const scenario={...data,settings:{...data.settings,compare_with_ortools:false}} as Scenario
beforeEach(()=>{
  window.localStorage.clear()
  Object.defineProperty(window,'innerWidth',{value:1280,configurable:true})
  vi.spyOn(api,'defaultScenario').mockResolvedValue(scenario)
  vi.spyOn(api,'solve').mockResolvedValue(normal as SolveResult)
})
afterEach(()=>vi.restoreAllMocks())

it('upute se pamte nakon zatvaranja i vraćaju iz pomoći',async()=>{
  const user=userEvent.setup()
  const {unmount}=render(<App/>)
  expect(screen.getByRole('region',{name:'Prvi koraci'})).toBeTruthy()
  await user.click(screen.getByRole('button',{name:'Zatvori prve korake'}))
  unmount()
  render(<App/>)
  expect(screen.queryByRole('region',{name:'Prvi koraci'})).toBeNull()
  await user.click(screen.getByRole('button',{name:'Pomoć'}))
  await user.click(screen.getByRole('button',{name:'Prikaži prve korake'}))
  expect(screen.getByRole('region',{name:'Prvi koraci'})).toBeTruthy()
})
it('na 390 px postavke su u ladici koja se otvara i zatvara',async()=>{
  Object.defineProperty(window,'innerWidth',{value:390,configurable:true})
  const user=userEvent.setup()
  render(<App/>)
  const trigger=await screen.findByRole('button',{name:'Postavke'})
  expect(screen.queryByRole('heading',{name:'Postavke'})).toBeNull()
  await user.click(trigger)
  expect(within(screen.getByRole('dialog',{name:'Postavke'})).getByRole('heading',{name:'Postavke'})).toBeTruthy()
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).toBeNull()
  expect(document.activeElement).toBe(trigger)
})
it('svih šest kartica dostupno je tipkovnicom',async()=>{
  const user=userEvent.setup()
  render(<App/>)
  const initial=screen.getByRole('tab',{name:'Plan'})
  expect(screen.getAllByRole('tab')).toHaveLength(6)
  initial.focus()
  await user.keyboard('{ArrowRight}')
  const map=screen.getByRole('tab',{name:'Karta'})
  expect(map.getAttribute('aria-selected')).toBe('true')
  expect(document.activeElement).toBe(map)
  await user.keyboard('{End}')
  expect(screen.getByRole('tabpanel',{name:'Ulazni podaci'})).toBeTruthy()
})
it('reset iz pomoći briše neispravan nacrt i kada je spremljena ista vrijednost',async()=>{
  const user=userEvent.setup()
  render(<App/>)
  const field=await screen.findByLabelText('Trajanje utovara')
  fireEvent.change(field,{target:{value:'abc'}})
  fireEvent.blur(field)
  expect(field.getAttribute('aria-invalid')).toBe('true')
  await user.click(screen.getByRole('button',{name:'Pomoć'}))
  await user.click(screen.getByRole('button',{name:'Vrati podatke i postavke iz zadatka'}))
  const clean=screen.getByLabelText('Trajanje utovara') as HTMLInputElement
  expect(clean.value).toBe('20')
  expect(clean.getAttribute('aria-invalid')).toBe('false')
})
it('klik na upozorenje otvara ulazne podatke i fokusira ispravan nalog',async()=>{
  const s=structuredClone(scenario)
  s.machines.push({id:'M11',weight_kg:12000})
  s.orders.push({id:'N11',machine:'M11',pickup:'L1',delivery:'L3'})
  vi.mocked(api.defaultScenario).mockResolvedValue(s)
  vi.mocked(api.solve).mockResolvedValue(heavy as SolveResult)
  render(<App/>)
  await userEvent.click(await screen.findByRole('button',{name:'Otvori nalog N11'}))
  expect(screen.getByRole('tabpanel',{name:'Ulazni podaci'})).toBeTruthy()
  await waitFor(()=>expect(document.activeElement?.id).toBe('order-N11'))
})
it('pala provjera sprječava prikaz rute i na kartici Karta',async()=>{
  const invalid={...normal,validation:{...normal.validation,passed:false}} as SolveResult
  vi.mocked(api.solve).mockResolvedValue(invalid)
  render(<App/>)
  await screen.findByRole('alert')
  await userEvent.click(screen.getByRole('tab',{name:'Karta'}))
  const panel=screen.getByRole('tabpanel',{name:'Karta'})
  expect(within(panel).getByRole('alert').textContent).toContain('Plan nije valjan')
  expect(within(panel).queryByTestId('loc-L0')).toBeNull()
})
