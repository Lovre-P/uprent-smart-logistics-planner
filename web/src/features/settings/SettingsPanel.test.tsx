import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import data from '../../../../data/default_scenario.json'
import type { Settings } from '../../types'
import { SettingsPanel } from './SettingsPanel'

const settings = data.settings as Settings
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
