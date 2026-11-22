import type { Scenario, Settings } from '../types'
import { SETTINGS_KEYS } from '../types'
import { formatKg } from '../lib/format'

export type Group = 'locations' | 'machines' | 'trucks' | 'orders'
export interface Column { key: string; title: string; type?: 'text' | 'number'; optional?: boolean; list?: Group }

export const groups: Record<Group, { title: string; noun: string; columns: Column[] }> = {
  locations: { title: 'Lokacije', noun: 'lokaciju', columns: [
    {key:'id', title:'Oznaka'}, {key:'name', title:'Naziv', optional:true},
    {key:'x', title:'X (km)',type:'number'}, {key:'y', title:'Y (km)',type:'number'},
  ] },
  machines: { title: 'Strojevi', noun: 'stroj', columns: [
    {key:'id', title:'Oznaka'},{key:'weight_kg', title:'Masa (kg)',type:'number'},
  ] },
  trucks: { title:'Kamioni', noun:'kamion', columns: [
    {key:'id', title:'Oznaka'},{key:'name', title:'Naziv', optional:true},
    {key:'capacity_kg', title:'Nosivost (kg)',type:'number'},{key:'slots', title:'Broj mjesta',type:'number'},
    {key:'speed_kmh', title:'Brzina (km/h)',type:'number'},
  ] },
  orders: { title:'Transportni nalozi', noun:'nalog', columns: [
    {key:'id', title:'Oznaka'},{key:'machine', title:'Stroj',list:'machines'},
    {key:'pickup', title:'Preuzimanje',list:'locations'},{key:'delivery',title:'Isporuka',list:'locations'},
    {key:'load_min', title:'Utovar (min)',type:'number',optional:true},
    {key:'unload_min',title:'Istovar (min)',type:'number',optional:true},
  ] },
}
const defaults: Settings = {
  day_limit_min: 540, limit_includes_handling: false, load_min: 20, unload_min: 20,
  require_all_trucks: false, allow_partial: true, objective:'km', solver:'auto',
  ortools_time_limit_s:3, compare_with_ortools:true, day_start:'07:00',
  exact_max_orders:12, exact_max_trucks:3, pinned_orders: null,
}

export class InputError extends Error {
  field: string
  constructor(field: string, message: string) {
    super(message)
    this.field = field
  }
}
function fail(key: string, message: string): never { throw new InputError(key, message) }
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('', 'Očekuje se JSON objekt.')
  return value as Record<string, unknown>
}
function onlyFields(obj: Record<string, unknown>, allowed: string[]) {
  const extra = Object.keys(obj).find(key => !allowed.includes(key))
  if (extra) fail(extra, 'Nepoznato polje: ' + extra + '.')
}
export function validateSetting(key: keyof Settings, value: unknown): void {
  const min = (strict = false) => {
    if (typeof value !== 'number' || !Number.isFinite(value) || (strict ? value <= 0 : value < 0))
      fail(key, strict ? 'Unesite broj veći od nule.' : 'Unesite nenegativan broj.')
  }
  switch (key) {
    case 'load_min': case 'unload_min': min(); break
    case 'day_limit_min': min(true); break
    case 'exact_max_orders': case 'exact_max_trucks':
      if (!Number.isInteger(value) || Number(value) < 1) fail(key, 'Unesite pozitivan cijeli broj.')
      break
    case 'ortools_time_limit_s':
      if (typeof value !== 'number' || !Number.isFinite(value) || value < 1 || value > 30) fail(key, 'Unesite vrijeme od 1 do 30 sekundi.')
      break
    case 'day_start':
      if (typeof value !== 'string' || !/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) fail(key, 'Unesite vrijeme u obliku HH:MM.')
      break
    case 'objective':
      if (value !== 'km' && value !== 'makespan') fail(key, 'Nepoznat cilj optimizacije.')
      break
    case 'solver':
      if (!['auto','exact','ortools'].includes(String(value))) fail(key, 'Nepoznat solver.')
      break
    case 'pinned_orders':
      if (value != null && Object.values(record(value)).some(truck => typeof truck !== 'string')) fail(key, 'Provjerite oznake prikvačenih naloga i kamiona.')
      break
    default:
      if (typeof value !== 'boolean') fail(key, 'Očekuje se uključena ili isključena postavka.')
  }
}

function readRows(group: Group, value: unknown) {
  if (!Array.isArray(value)) fail(group, 'Nedostaje popis: ' + groups[group].title + '.')
  if (!value.length && (group === 'locations' || group === 'trucks'))
    fail(group, group === 'trucks' ? 'Potreban je barem jedan kamion.' : 'Potrebna je barem jedna lokacija.')
  const ids = new Set<string>()
  return value.map((item: unknown) => {
    const row = {...record(item)}
    if (group === 'trucks' && row.speed_kmh === undefined) row.speed_kmh = 60
    const columns = groups[group].columns
    onlyFields(row, columns.map(c => c.key))
    for (const {key,title,type,optional} of columns) {
      const v = row[key]
      if (optional && v == null) continue
      if (type !== 'number') {
        if (typeof v !== 'string' || (!optional && !v.trim())) fail(key, 'Upišite polje ' + title + '.')
      } else if (typeof v !== 'number' || !Number.isFinite(v)) fail(key, 'Unesite broj za polje ' + title + '.')
      else if (['slots','weight_kg','capacity_kg'].includes(key) && (!Number.isInteger(v) || v < 1))
        fail(key, 'Za polje ' + title + ' unesite pozitivan cijeli broj.')
      else if (key === 'speed_kmh' && v <= 0) fail(key, 'Brzina mora biti veća od nule.')
      else if (['load_min','unload_min'].includes(key) && v < 0) fail(key, 'Trajanje mora biti nenegativno.')
    }
    const id = String(row.id)
    if (ids.has(id)) fail('id', 'Oznaka ' + id + ' već postoji u tablici.')
    ids.add(id)
    return row
  })
}

export function readScenario(raw: unknown): Scenario {
  const obj = record(raw)
  onlyFields(obj, ['name', 'depot', 'locations','machines','trucks','orders','settings'])
  if (typeof obj.name !== 'string') fail('name', 'Nedostaje naziv scenarija.')
  const settings = {...defaults, ...record(obj.settings === undefined ? {} : obj.settings)}
  onlyFields(settings, [...SETTINGS_KEYS])
  for (const key of SETTINGS_KEYS) validateSetting(key, settings[key])
  const scenario = {...obj, settings} as unknown as Scenario
  for (const group of Object.keys(groups) as Group[]) {
    Object.assign(scenario, {[group]: readRows(group, obj[group])})
  }
  const locations = new Set(scenario.locations.map(x => x.id))
  if (!locations.has(scenario.depot)) fail('depot', 'Baza ' + String(scenario.depot) + ' mora biti među lokacijama.')
  const machines = new Map(scenario.machines.map(x => [x.id, x]))
  const assigned = new Set<string>()
  for (const order of scenario.orders) {
    for (const key of ['pickup','delivery'] as const)
      if (!locations.has(order[key])) fail(key, order.id + ': nepoznata lokacija ' + order[key] + '.')
    if (order.pickup === order.delivery) fail('delivery', order.id + ': preuzimanje i isporuka moraju biti na različitim lokacijama.')
    if (!machines.has(order.machine)) fail('machine', order.id + ': nepoznat stroj ' + order.machine + '.')
    if (assigned.has(order.machine)) fail('machine', order.machine + ' već je dodijeljen drugom nalogu.')
    assigned.add(order.machine)
  }
  for (const [oid, tid] of Object.entries(settings.pinned_orders ?? {})) {
    const order = scenario.orders.find(x => x.id === oid)
    const truck = scenario.trucks.find(x => x.id === tid)
    if (!order || !truck) fail('pinned_orders', 'Prikvačeni nalog ' + oid + ' ili kamion ' + tid + ' više ne postoji.')
    if (machines.get(order.machine)!.weight_kg > truck.capacity_kg)
      fail('pinned_orders', oid + ' prelazi nosivost kamiona ' + tid + ' (' + formatKg(truck.capacity_kg) + ').')
  }
  return scenario
}
