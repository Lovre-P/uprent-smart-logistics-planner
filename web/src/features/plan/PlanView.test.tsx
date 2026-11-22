import { fireEvent, render, screen, within } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import data from '../../../../data/default_scenario.json'
import normal from '../../test/fixtures/default-result.json'
import heavy from '../../test/fixtures/n11-result.json'
import type { Scenario, SolveResult } from '../../types'
import { formatKg } from '../../lib/format'
import { PlanView } from './PlanView'
import { ValidationView } from '../validation/ValidationView'

const scenario = data as Scenario
const standard = normal as SolveResult
function show(result = standard) {
  const applySettings = vi.fn()
  const onOrder = vi.fn()
  render(<PlanView {...{result, scenario, applySettings, onOrder}} />)
  return {applySettings, onOrder}
}
it('prikazuje sažetak naloga i kilometražu', () => {
  show()
  const totals = screen.getByRole('region', {name:'Sažetak plana'})
  expect(within(totals).getByText('182,2 km')).toBeTruthy()
  expect(within(totals).getByText('10/10')).toBeTruthy()
  expect(within(totals).getByText('1 od 2')).toBeTruthy()
})
it('objašnjava nekorišteni kamion', () => {
  show()
  const a = screen.getByRole('article', {name:'Kamion A'})
  expect(a.textContent).toContain('nije korišten')
  fireEvent.click(within(a).getByRole('button',{name:/zašto/i}))
  expect(a.textContent).toContain(standard.analysis.unused_trucks[0].message)
})
it('tablica B sadrži svih 21 korak, povratak i teret prvog koraka', () => {
  show()
  const peak = standard.trucks.find(truck=>truck.id==='B')!
  expect(screen.getByRole('article', {name:'Kamion B'}).textContent)
    .toContain(Math.round(100 * peak.peak_kg / peak.capacity_kg) + ' %')
  const table = screen.getByRole('table',{name:'Koraci rute: Kamion B'})
  const steps = within(table).getAllByRole('row').slice(1)
  expect(steps).toHaveLength(21)
  const first = standard.trucks.find(truck=>truck.id==='B')!.steps[0]
  expect(steps[0].textContent).toContain(first.location)
  expect(steps[0].textContent).toContain(formatKg(first.load_kg))
  expect(steps.at(-1)?.textContent).toContain('Povratak')
})
it('primjenjuje alternativno tumačenje limita', () => {
  const {applySettings} = show()
  const strip = screen.getByRole('region',{name:'Drugo tumačenje'})
  expect(strip.textContent).toContain('200,1 km')
  fireEvent.click(within(strip).getByRole('button',{name:'Primijeni'}))
  expect(applySettings).toHaveBeenCalledWith({limit_includes_handling:true})
})
it('upozorenje za N11 otvara pripadajući nalog', () => {
  const {onOrder} = show(heavy as SolveResult)
  const warning = screen.getByRole('region',{name:'Neizvršeni nalozi'})
  expect(warning.textContent).toContain('TOO_HEAVY')
  fireEvent.click(within(warning).getByRole('button',{name:/N11/}))
  expect(onOrder).toHaveBeenCalledWith('N11')
})
it('provjera prikazuje svih deset pravila i njihove ishode', () => {
  render(<ValidationView result={standard} comparison={null} />)
  const checks=within(screen.getByRole('list',{name:'Provjerena pravila'})).getAllByRole('listitem')
  expect(checks).toHaveLength(10)
  for (const item of checks) expect(item.textContent).toContain('✓')
})
it.each(['NO_FULL_PLAN','INVALID_PLAN','NOT_FOUND'] as const)('za %s skriva kilometre, rute i alternativne dodjele', status => {
  show({...standard,status,optimality:'none'})
  expect(screen.queryByRole('region',{name:'Sažetak plana'})).toBeNull()
  expect(screen.queryByRole('table')).toBeNull()
  expect(screen.queryByRole('button',{name:'Primijeni'})).toBeNull()
})
it('ne prikazuje plan nakon neuspješne tvrde provjere bez obzira na status', () => {
  show({...standard,validation:{...standard.validation,passed:false}})
  expect(screen.getByRole('alert').textContent).toContain('Plan nije valjan')
  expect(screen.queryByRole('table')).toBeNull()
})
it('odvaja informativnu provjeru od pada tvrde provjere', () => {
  const checks=standard.validation.checks.map(c=>c.rule==='svi_kamioni'?{...c,passed:false}:c)
  render(<ValidationView result={{...standard,validation:{passed:true,checks}}} comparison={null}/>)
  expect(screen.getByText('Napomena')).toBeTruthy()
  expect(screen.queryByRole('alert')).toBeNull()
})
