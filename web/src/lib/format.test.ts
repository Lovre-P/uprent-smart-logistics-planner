import { describe, expect, it } from 'vitest'
import { formatDuration, formatKg, formatKm } from './format'
import { parseHrNumber } from './parseNumber'

describe('Brojke u hrvatskom formatu', () => {
  it('prikazuje decimalne kilometre i tisućice kilograma', () => {
    expect(formatKm(182.2)).toBe('182,2 km')
    expect(formatKg(9400)).toBe('9.400 kg')
  })
  it.each([[582.2, '9 h 42 min'], [522.9, '8 h 43 min'], [37.2, '37 min'], [540, '9 h'], [182.2, '3 h 02 min']])(
    'prikazuje trajanje %s', (value, result) => expect(formatDuration(Number(value))).toBe(result),
  )
  it.each([['20,5', 20.5], ['20.5', 20.5], ['0', 0], ['abc', null], ['', null], ['20,5.0', null]])(
    'čita decimalni unos %s', (input, result) => expect(parseHrNumber(String(input))).toBe(result),
  )
})
