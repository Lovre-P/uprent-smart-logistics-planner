import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import data from '../../../../data/default_scenario.json'
import type { Scenario, Settings } from '../../types'
import { useScenario } from '../../state/useScenario'
import { api } from '../../api'
import { SettingsPanel } from './SettingsPanel'

const settings = data.settings as Settings
afterEach(() => vi.restoreAllMocks())

it.each(['Vrati zadano', 'Učitaj drugi scenarij'])('uklanja nevaljani nacrt nakon radnje %s', async action => {
  const initial = structuredClone(data) as Scenario
  vi.spyOn(api, 'defaultScenario').mockResolvedValue(initial)
  function Panel() {
    const state = useScenario()
    if (!state.scenario) return null
    return <>
      <SettingsPanel key={state.formRevision} settings={state.scenario.settings} onChange={state.applySettings}/>
      <button onClick={state.resetToTask}>Vrati zadano</button>
      <button onClick={() => state.setScenario({...initial, name:'Drugi'})}>Učitaj drugi scenarij</button>
    </>
  }
  render(<Panel/>)
  const input = await screen.findByLabelText('Trajanje utovara') as HTMLInputElement
  fireEvent.change(input, {target:{value:'abc'}})
  fireEvent.blur(input)
  expect(input.getAttribute('aria-invalid')).toBe('true')
  await userEvent.click(screen.getByRole('switch', {name:/Svaki kamion/}))
  expect(input.value).toBe('abc')
  await userEvent.click(screen.getByRole('button', {name:action}))
  const restored = screen.getByLabelText('Trajanje utovara') as HTMLInputElement
  expect(restored.value).toBe('20')
  expect(restored.getAttribute('aria-invalid')).toBe('false')
  expect(screen.queryByRole('alert')).toBeNull()
})
it('prikazuje doslovne postavke zadatka', () => {
  render(<SettingsPanel settings={settings} onChange={() => {}} />)
  expect(screen.getByText('9 h')).toBeTruthy()
  expect((screen.getByRole('switch', {name: /U 9 h/}) as HTMLInputElement).checked).toBe(false)
  expect((screen.getByRole('switch', {name: /Svaki kamion/}) as HTMLInputElement).checked).toBe(false)
  expect((screen.getByLabelText(/^Trajanje utovara$/) as HTMLInputElement).value).toBe('20')
  expect((screen.getByLabelText(/^Trajanje istovara$/) as HTMLInputElement).value).toBe('20')
})
it('promjena prekidača šalje samo izmijenjenu postavku', async () => {
  const patch = vi.fn()
  render(<SettingsPanel settings={settings} onChange={patch} />)
  await userEvent.click(screen.getByRole('switch', { name: /U 9 h/ }))
  expect(patch).toHaveBeenCalledWith({limit_includes_handling: true})
})
it('svaka vidljiva postavka ima uputu', () => {
  render(<SettingsPanel settings={{...settings,pinned_orders:{N03:'A'}}} onChange={() => {}} />)
  const rows = document.querySelectorAll('[data-setting]')
  expect(rows.length).toBe(14)
  for (const row of rows) expect(within(row as HTMLElement).getByRole('button', { name: /^Uputa:/, hidden: true })).toBeTruthy()
})
it('prihvaća decimalni zarez u minutama i zadržava nevaljani unos', () => {
  const patch = vi.fn()
  render(<SettingsPanel settings={settings} onChange={patch} />)
  const input = screen.getByLabelText(/^Trajanje utovara$/)
  fireEvent.change(input, {target:{ value: '20,5' }})
  fireEvent.blur(input)
  expect(patch).toHaveBeenLastCalledWith({load_min:20.5})
  patch.mockClear()
  fireEvent.change(input, {target:{ value: 'abc' }})
  fireEvent.blur(input)
  expect(input.getAttribute('aria-invalid')).toBe('true')
  expect(patch).not.toHaveBeenCalled()
})
