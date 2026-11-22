import { fireEvent, render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import data from '../../../../data/default_scenario.json'
import normal from '../../test/fixtures/default-result.json'
import strict from '../../test/fixtures/strict-result.json'
import type { Scenario, SolveResult } from '../../types'
import { MapView } from './MapView'

const scenario = data as Scenario
const standard = normal as SolveResult

it('ucrtava svih deset lokacija uz jednako mjerilo po osima i koordinate u km', () => {
  render(<MapView scenario={scenario} result={standard} />)
  expect(screen.getAllByTestId(/^loc-/)).toHaveLength(10)
  const xy = (id: string) => {
    const el = screen.getByTestId('loc-' + id)
    return [Number(el.getAttribute('data-x')), Number(el.getAttribute('data-y'))]
  }
  const [ox, oy] = xy('L0')
  const [x, y] = xy('L1')
  expect((x - ox) / 3).toBeCloseTo((oy - y) / 8)
  expect(screen.getByText('X (km)')).toBeTruthy()
  expect(screen.getByText('Y (km)')).toBeTruthy()
})

it.each([[standard, 1], [strict as SolveResult, 2]] as const)('crta rutu samo za kamione koji voze', (result, count) => {
  render(<MapView scenario={scenario} result={result} />)
  expect(screen.getAllByTestId(/^route-/)).toHaveLength(count)
  const steps = result.trucks.flatMap(t => t.steps)
  expect(screen.getAllByRole('button', {name: /korak \d+/i})).toHaveLength(steps.length)
  const arrows = document.querySelectorAll('polyline[marker-mid]')
  expect(arrows).toHaveLength(steps.filter(s => s.leg_km > 0).length)
})

it('otkriva detalje svakog koraka fokusom, mišem i dodirom, uključujući povratak', () => {
  render(<MapView scenario={scenario} result={standard} />)
  const steps = standard.trucks[1].steps
  const markers = screen.getAllByRole('button', {name:/Kamion B.*korak \d+/i})
  fireEvent.focus(markers[0])
  expect(screen.getByRole('status').textContent).toContain(steps[0].order)
  fireEvent.mouseEnter(markers[1])
  expect(screen.getByRole('status').textContent).toContain(steps[1].order)
  fireEvent.click(markers.at(-1)!)
  expect(screen.getByRole('status').textContent).toMatch(/Povratak.*L0/)
})
