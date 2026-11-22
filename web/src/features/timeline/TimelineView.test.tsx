import { fireEvent, render, screen, within } from '@testing-library/react'
import { expect, it } from 'vitest'
import data from '../../../../data/default_scenario.json'
import normal from '../../test/fixtures/default-result.json'
import strict from '../../test/fixtures/strict-result.json'
import type { Scenario, SolveResult } from '../../types'
import { TimelineView } from './TimelineView'

const scenario = data as Scenario
const standard = normal as SolveResult
const sum = (segments: HTMLElement[]) => segments.reduce((total, el) => total + Number(el.dataset.minutes), 0)

it('20 radnji, pozitivne dionice i zbroj vremena vožnje od 182,2 minute', () => {
  render(<TimelineView scenario={scenario} result={standard} />)
  const truck = within(screen.getByRole('article', {name:'Kamion B'}))
  const actions = truck.getAllByRole('button', {name:/Utovar|Istovar/})
  const drives = truck.getAllByRole('button', {name:/Vožnja/})
  expect(actions).toHaveLength(20)
  expect(sum(actions)).toBe(400)
  expect(drives.every(el => Number(el.dataset.minutes) > 0)).toBe(true)
  expect(sum(drives)).toBeCloseTo(182.2)
  expect(truck.getByTestId('limit-drive')).toBeTruthy()
  expect(truck.getByText(/samo vožnja/i)).toBeTruthy()
  expect(truck.queryByTestId('limit-work')).toBeNull()
  fireEvent.focus(actions[0])
  expect(truck.getByRole('status').textContent).toContain(standard.trucks[1].steps[0].order)
})

it('prikazuje ograničenje cijelog dana na vremenskoj osi strogog plana', () => {
  render(<TimelineView scenario={scenario} result={strict as SolveResult} />)
  const truck = within(screen.getByRole('article', {name:'Kamion B'}))
  expect(truck.getByText(/vožnja i radnje/i)).toBeTruthy()
  expect(truck.getByTestId('limit-work')).toBeTruthy()
  expect(truck.queryByTestId('limit-drive')).toBeNull()
})

it('čuva nulu i trajanje naloga te brzinu kamiona pri računanju segmenata', () => {
  const revised: Scenario = {...scenario,
    trucks: scenario.trucks.map(t => ({...t, speed_kmh:45})),
    orders: scenario.orders.map(o => o.id === 'N01' ? {...o, load_min:0, unload_min:7.25} : o),
  }
  render(<TimelineView scenario={revised} result={standard} />)
  const truck = within(screen.getByRole('article', {name:'Kamion B'}))
  expect(truck.getByRole('button', {name:/Utovar.*N01/}).dataset.minutes).toBe('0')
  expect(truck.getByRole('button', {name:/Istovar.*N01/}).dataset.minutes).toBe('7.25')
  expect(sum(truck.getAllByRole('button', {name:/Vožnja/}))).toBeCloseTo(182.2 * 60 / 45)
})
