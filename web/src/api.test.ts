import { afterEach, expect, it, vi } from 'vitest'
import { api } from './api'
import type { Scenario } from './types'

afterEach(() => vi.unstubAllGlobals())
it('šalje scenarij i omogućuje prekid zahtjeva', async () => {
  const request = vi.fn().mockResolvedValue(Response.json({}))
  vi.stubGlobal('fetch', request)
  const signal = new AbortController().signal
  await api.solve({name: 'Primjer'} as Scenario, signal)
  const [url, init] = request.mock.calls[0]
  expect(url).toBe('/api/solve')
  expect(init.signal).toBe(signal)
  expect(JSON.parse(init.body)).toEqual({scenario: {name: 'Primjer'}})
})
it('prenosi poruku poslužitelja za neispravan unos', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({detail: 'N01: nepoznata lokacija'}, {status: 422})))
  await expect(api.defaultScenario()).rejects.toThrow('N01: nepoznata lokacija')
})
