import { useLayoutEffect, useRef, useState } from 'react'
import { api } from '../api'
import { hasUsablePlan } from '../lib/plan'
import type { Scenario, SolveResult } from '../types'

export function useSolve(scenario: Scenario | null) {
  const sequence = useRef(0)
  const [manual, setManual] = useState<{scenario: Scenario; detailed: boolean} | null>(null)
  const [accepted, setAccepted] = useState<{result:SolveResult;scenario:Scenario} | null>(null)
  const [comparison, setComparison] = useState<SolveResult | null>(null)
  const [computing, setComputing] = useState(false)
  const [comparing, setComparing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [comparisonError, setComparisonError] = useState<string | null>(null)

  useLayoutEffect(() => {
    const ticket = ++sequence.current
    const controller = new AbortController()
    const current = () => sequence.current === ticket && !controller.signal.aborted
    setError(null)
    setComparisonError(null)
    setComparison(null)
    setComputing(!!scenario)
    setComparing(false)
    if (!scenario) {
      setAccepted(null)
      return
    }
    const input = scenario
    const requested = manual?.scenario === scenario ? manual : null
    const lookup = async () => {
      let result: SolveResult
      try {
        result = await api.solve(input, controller.signal, requested?.detailed)
      } catch (e) {
        if (current()) { setError((e as Error).message); setComputing(false) }
        return
      }
      if (!current()) return
      setAccepted({result,scenario:input})
      setComputing(false)
      if (result.solver !== 'exact' || !input.settings.compare_with_ortools || !hasUsablePlan(result)) return
      setComparing(true)
      try {
        const alternate = {...input, settings:{...input.settings,solver:'ortools' as const,compare_with_ortools:false}}
        const value = await api.solve(alternate,controller.signal)
        if (current()) setComparison(value)
      } catch (e) {
        if (current()) setComparisonError((e as Error).message)
      } finally {
        if (current()) setComparing(false)
      }
    }
    const timeout = window.setTimeout(() => { void lookup() }, requested ? 0 : 300)
    return () => {
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [scenario, manual])

  function recalculate(detailed = false) {
    if (scenario) setManual({scenario,detailed})
  }
  return { result:accepted?.result ?? null, resultScenario:accepted?.scenario ?? null, comparison,
    computing, comparing, error, comparisonError, recalculate }
}
