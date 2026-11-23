const integer = new Intl.NumberFormat('hr-HR', { useGrouping: 'always', maximumFractionDigits: 0 })
const distance = new Intl.NumberFormat('hr-HR', { useGrouping: 'always', minimumFractionDigits: 1, maximumFractionDigits: 1 })

export function formatKm(km: number): string {
  return distance.format(km) + ' km'
}
export function formatKg(kg: number): string {
  return integer.format(kg) + ' kg'
}
export function formatDuration(minutes: number): string {
  const total = Math.round(Math.abs(minutes))
  const hours = Math.floor(total / 60)
  const remainder = total % 60
  const sign = minutes < 0 && total > 0 ? '−' : ''
  if (hours === 0) return sign + remainder + ' min'
  return sign + hours + ' h' + (remainder ? ' ' + String(remainder).padStart(2, '0') + ' min' : '')
}
