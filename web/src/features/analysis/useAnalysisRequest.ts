import { useEffect, useRef, useState } from 'react'

export function useAnalysisRequest<T>(scenario: object, result?: object) {
  const [value, setValue] = useState<T | null>(null)
  const [waiting, setWaiting] = useState(false)
  const [error, setError] = useState('')
  const active = useRef<AbortController | null>(null)

  useEffect(() => {
    setValue(null)
    setWaiting(false)
    setError('')
    return () => active.current?.abort()
  }, [scenario, result])

  async function run(request: (signal: AbortSignal) => Promise<T>) {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setWaiting(true)
    setError('')
    try {
      const next = await request(controller.signal)
      if (!controller.signal.aborted) setValue(next)
    } catch (cause) {
      if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Izračun nije uspio.')
    } finally {
      if (!controller.signal.aborted) setWaiting(false)
    }
  }
  return {value, waiting, error, run}
}
