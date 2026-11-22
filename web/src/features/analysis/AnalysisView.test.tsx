import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import scenarioData from '../../../../data/default_scenario.json'
import defaultResult from '../../test/fixtures/default-result.json'
import strictResult from '../../test/fixtures/strict-result.json'
import { api } from '../../api'
import type { ComparisonRow, Scenario, SolveResult } from '../../types'
import { AnalysisView } from './AnalysisView'

const scenario = scenarioData as Scenario
const result = defaultResult as SolveResult
const strict = strictResult as SolveResult
const makeProps = () => ({ scenario, result, applySettings: vi.fn(), onDetailed: vi.fn() })
afterEach(() => vi.restoreAllMocks())

it('prikazuje učinak premještanja i čuva postojeće prikvačene naloge', async () => {
  const p = makeProps()
  p.scenario = {...scenario, settings: {...scenario.settings, pinned_orders: {N05: 'B'}}}
  render(<AnalysisView {...p}/>)
  expect(within(screen.getByRole('row', {name:/N03 B A/})).getByText('+17,9 km')).toBeTruthy()
  const row = screen.getByRole('row', {name:/N04 B A/})
  await userEvent.click(within(row).getByRole('button', {name:'Prikaži plan'}))
  expect(p.applySettings).toHaveBeenCalledWith({pinned_orders: {N04:'A', N05:'B'}})
})

it('svaka točka krivulje odabire cijelu raspodjelu', async () => {
  const p = makeProps()
  render(<AnalysisView {...p}/>)
  const buttons = screen.getAllByRole('button', {name:/^Prikaži raspored/})
  expect(buttons).toHaveLength(14)
  await userEvent.click(buttons.at(-1)!)
  const pins = p.applySettings.mock.calls[0][0].pinned_orders
  expect(Object.keys(pins)).toHaveLength(10)
  expect([pins.N01, pins.N05, pins.N06, pins.N10]).toEqual(['A','A','B','B'])
})

it('prikazuje točan prag osjetljivosti i omogućuje odgođeni izračun', async () => {
  const p = makeProps()
  const mounted = render(<AnalysisView {...p} result={strict}/>)
  expect(screen.getAllByText(/20,95 min/).length).toBeGreaterThan(0)
  const slow = {...result, analysis:{...result.analysis, sensitivity:{...result.analysis.sensitivity,
    limit_lower_min:null, note:'Druga tumačenja i osjetljivost dostupni su na zahtjev.'}}}
  mounted.rerender(<AnalysisView {...p} result={slow}/>)
  await userEvent.click(screen.getByRole('button', {name:/izračunaj osjetljivost/i}))
  expect(p.onDetailed).toHaveBeenCalledOnce()
})

it('lijeni redak provjerava stvarni ishod prije primjene', async () => {
  const p = makeProps()
  const lazy = {...result, analysis:{...result.analysis, why: result.analysis.why.map(row=>({...row,lazy:true}))}}
  const request = vi.spyOn(api, 'solve').mockResolvedValue(strict)
  render(<AnalysisView {...p} result={lazy}/>)
  const n03 = within(screen.getByRole('row', {name:/N03 B A/}))
  await userEvent.click(n03.getByRole('button', {name:'Izračunaj'}))
  expect(request.mock.calls[0][0].settings.pinned_orders).toEqual({N03:'A'})
  expect(await n03.findByText('+17,9 km')).toBeTruthy()
  await userEvent.click(n03.getByRole('button', {name:'Prikaži plan'}))
  expect(p.applySettings).toHaveBeenCalledWith({pinned_orders:{N03:'A'}})
  const n04 = within(screen.getByRole('row', {name:/N04 B A/}))
  await userEvent.click(n04.getByRole('button', {name:'Izračunaj'}))
  expect(await n04.findByText(/nije prevezen/)).toBeTruthy()
  expect(n04.queryByRole('button', {name:'Prikaži plan'})).toBeNull()
})

it('usporedba prikazuje svih šest odgovora API-ja uz tumačenja', async () => {
  const rows = Array.from({length:6}, (_,i)=>({label:'Scenarij ' + i, km:180+i, served:10,
    orders:10, trucks_used:1, valid_under:['samo vožnja']}))
  const request = vi.spyOn(api, 'compare').mockResolvedValue(rows)
  render(<AnalysisView {...makeProps()}/>)
  await userEvent.click(screen.getByRole('button', {name:'Usporedi scenarije'}))
  const table = await screen.findByRole('table', {name:'Usporedba scenarija'})
  expect(request.mock.calls[0][0]).toEqual(scenario)
  expect(within(table).getAllByRole('row')).toHaveLength(7)
  expect(within(table).getAllByText('samo vožnja')).toHaveLength(6)
})

it('kasni odgovor usporedbe ne zamjenjuje noviji scenarij', async () => {
  let finish!: (rows: ComparisonRow[]) => void
  const comparison = vi.spyOn(api, 'compare').mockReturnValueOnce(new Promise(resolve => { finish = resolve }))
    .mockResolvedValue([{label:'Noviji primjer',km:200.1,served:10,orders:10,trucks_used:2,valid_under:[]}])
  const p = makeProps()
  const mounted = render(<AnalysisView {...p}/>)
  await userEvent.click(screen.getByRole('button', {name:'Usporedi scenarije'}))
  mounted.rerender(<AnalysisView {...p} scenario={{...scenario, name:'Drugi scenarij'}}/>)
  await userEvent.click(screen.getByRole('button', {name:'Usporedi scenarije'}))
  await screen.findByText('Noviji primjer')
  await act(async () => finish([]))
  expect(screen.getByText('Noviji primjer')).toBeTruthy()
  expect(comparison).toHaveBeenCalledTimes(2)
})
