import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Scenario, Settings } from '../types'
import { readScenario } from './scenarioValidation'

export function useScenario() {
  const [scenario, update] = useState<Scenario | null>(null)
  const [formRevision, refreshForms] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const original = useRef<Scenario | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    api.defaultScenario(controller.signal).then(raw => {
      if (controller.signal.aborted) return
      original.current = readScenario(raw)
      update(structuredClone(original.current))
    }).catch((e: Error) => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [])

  function accept(value: Scenario, replaceForms: boolean) {
    try {
      const valid = readScenario(value)
      update(valid)
      setError(null)
      if (replaceForms) refreshForms(n => n + 1)
    } catch (e) { setError((e as Error).message) }
  }
  function setScenario(value: Scenario) {
    accept(value, true)
  }
  function applySettings(patch: Partial<Settings>) {
    if (scenario) accept({...scenario, settings:{...scenario.settings,...patch}}, false)
  }
  function resetToTask() {
    if (original.current) setScenario(original.current)
  }
  return { scenario, setScenario, applySettings, resetToTask, formRevision, error }
}
