import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import data from '../../../data/default_scenario.json'
import { api } from '../api'
import type { Scenario } from '../types'
import { useScenario } from './useScenario'

afterEach(() => vi.restoreAllMocks())
it('vraća zadane podatke i postavke nakon izmjena', async () => {
  vi.spyOn(api, 'defaultScenario').mockResolvedValue(structuredClone(data) as Scenario)
  const {result} = renderHook(() => useScenario())
  await waitFor(() => expect(result.current.scenario).toBeTruthy())
  act(() => result.current.applySettings({load_min: 25}))
  expect(result.current.scenario?.settings.load_min).toBe(25)
  act(() => result.current.resetToTask())
  expect(result.current.scenario?.orders).toEqual(data.orders)
  expect(result.current.scenario?.settings.load_min).toBe(20)
})
