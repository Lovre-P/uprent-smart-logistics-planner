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

it('označava podudarne lokacije zajedničkim natpisom umjesto dvaju preklopljenih natpisa', () => {
  const locations = scenario.locations.map(l => l.id === 'L1' ? {...l, x:0, y:0} : l)
  render(<MapView scenario={{...scenario, locations}} result={standard} />)
  expect(screen.getAllByTestId(/^loc-/)).toHaveLength(10)
  expect(screen.getByTestId('loc-L0').closest('text')?.textContent).toBe('L0 / L1 · Baza')
  expect(screen.getByTestId('loc-L0').closest('text')).toBe(screen.getByTestId('loc-L1').closest('text'))
})

it('smješta naziv L7 ispod koraka i ostavlja prostor iznad oznaka donje osi', () => {
  render(<MapView scenario={scenario} result={standard} />)
  const location = screen.getByTestId('loc-L7')
  const pointY = Number(location.getAttribute('data-y'))
  const labelY = pointY + Number(location.closest('text')!.getAttribute('y'))
  const axisY = Number(screen.getByText('X (km)').getAttribute('y'))
  const badges = screen.getAllByRole('button', {name:/· L7 ·/})
  for (const badge of badges) {
    const match = badge.getAttribute('transform')!.match(/translate\(\S+ (\S+)\)/)!
    const radius = Number(badge.querySelector('circle')!.getAttribute('r'))
    expect(Number(match[1]) + radius).toBeLessThan(pointY)
  }
  expect(labelY).toBeGreaterThan(pointY + 10)
  expect(labelY + 12).toBeLessThan(axisY)
})
