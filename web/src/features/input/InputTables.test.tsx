import { render, screen, fireEvent, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { expect, it, vi } from 'vitest'
import data from '../../../../data/default_scenario.json'
import type { Scenario } from '../../types'
import { InputTables } from './InputTables'

function setup() {
  const changed = vi.fn()
  function Editor() {
    const [scenario, set] = useState<Scenario>(structuredClone(data) as Scenario)
    return <InputTables scenario={scenario} onChange={s => { changed(s); set(s) }} />
  }
  render(<Editor />)
  return changed
}

it('nepoznata lokacija daje grešku uz polje i zadržava zadnji valjani scenarij', async () => {
  const changed = setup()
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', {name:'Uredi N01'}))
  const input = screen.getByLabelText('Preuzimanje')
  fireEvent.change(input, {target: {value:'L99'}})
  await user.click(screen.getByRole('button', {name:'Spremi nalog'}))
  expect(screen.getByRole('alert').textContent).toMatch(/nepoznata lokacija/i)
  expect(input.getAttribute('aria-invalid')).toBe('true')
  expect(changed).not.toHaveBeenCalled()
})
it('dodaje M11 od 12.000 kg i nalog N11', async () => {
  const changed = setup()
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', {name:'Dodaj stroj'}))
  fireEvent.change(screen.getByLabelText('Masa (kg)'), {target:{value:'12000'}})
  await user.click(screen.getByRole('button', {name:'Spremi stroj'}))
  await user.click(screen.getByRole('button', {name:'Dodaj nalog'}))
  fireEvent.change(screen.getByLabelText('Stroj'), {target:{value:'M11'}})
  fireEvent.change(screen.getByLabelText('Preuzimanje'), {target:{value:'L1'}})
  fireEvent.change(screen.getByLabelText('Isporuka'), {target:{value:'L3'}})
  await user.click(screen.getByRole('button', {name:'Spremi nalog'}))
  const scenario = changed.mock.lastCall?.[0] as Scenario
  expect(scenario.orders).toHaveLength(11)
  expect(scenario.orders.at(-1)).toMatchObject({id:'N11',machine:'M11',pickup:'L1',delivery:'L3'})
  expect(scenario.machines.at(-1)?.weight_kg).toBe(12000)
})
it('brisanje korištene lokacije ostavlja nalog i javlja vezu', async () => {
  const changed = setup()
  await userEvent.click(screen.getByRole('button', {name:'Obriši L1'}))
  expect(screen.getByRole('alert').textContent).toMatch(/N01|L1/)
  expect(changed).not.toHaveBeenCalled()
})
it('uvoz neispravnog JSON-a ostavlja valjane tablice', async () => {
  const changed = setup()
  const raw = structuredClone(data)
  raw.orders[0].pickup = 'Q'
  const file = new File([JSON.stringify(raw)], 'scenarij.json', {type:'application/json'})
  await userEvent.upload(screen.getByLabelText('Uvezi JSON'), file)
  expect((await screen.findByRole('alert')).textContent).toMatch(/nepoznata lokacija/i)
  expect(within(screen.getByRole('table', {name:'Transportni nalozi'})).getByText('N01')).toBeTruthy()
  expect(changed).not.toHaveBeenCalled()
})
