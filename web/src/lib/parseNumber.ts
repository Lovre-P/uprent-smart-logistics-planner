export function parseHrNumber(input: string): number | null {
  const value = input.trim()
  if (!/^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)$/.test(value)) return null
  const number = Number(value.replace(',', '.'))
  return Number.isFinite(number) ? number : null
}
