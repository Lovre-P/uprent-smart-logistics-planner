import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Scenario, Settings } from '../types'
import { readScenario } from './scenarioValidation'

export function useScenario() {
  const [scenario, update] = useState<Scenario | null>(null)
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

  function setScenario(value: Scenario) {
    try {
      const valid = readScenario(value)
      update(valid)
      setError(null)
    } catch (e) { setError((e as Error).message) }
  }
  function applySettings(patch: Partial<Settings>) {
    if (scenario) setScenario({...scenario, settings:{...scenario.settings,...patch}})
  }
  function resetToTask() {
    if (original.current) { update(structuredClone(original.current)); setError(null) }
  }
  return { scenario, setScenario, applySettings, resetToTask, error }
}
