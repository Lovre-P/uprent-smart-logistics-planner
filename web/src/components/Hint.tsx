import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'
import { hints } from '../content/hints'

export function Hint({ id }: { id: keyof typeof hints.settings }) {
  const text = hints.settings[id]
  const popupId = useId()
  const trigger = useRef<HTMLButtonElement>(null)
  const popup = useRef<HTMLSpanElement>(null)
  const [open, setOpen] = useState(false)
  const [position, setPosition] = useState({ left: 0, top: 0 })

  useLayoutEffect(() => {
    if (!open) return
    const place = () => {
      const anchor = trigger.current?.getBoundingClientRect()
      const bubble = popup.current?.getBoundingClientRect()
      if (!anchor || !bubble) return
      const left = Math.max(8, Math.min(anchor.left, window.innerWidth - bubble.width - 8))
      const top = anchor.bottom + bubble.height + 8 <= window.innerHeight
        ? anchor.bottom + 5 : Math.max(8, anchor.top - bubble.height - 5)
      setPosition({ left, top })
    }
    place()
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const outside = (event: PointerEvent) => {
      const node = event.target
      if (node instanceof Node && !trigger.current?.contains(node) && !popup.current?.contains(node)) setOpen(false)
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', outside)
      document.removeEventListener('keydown', escape)
    }
  }, [open])

  return <>
    <button ref={trigger} className="hint-trigger" type="button"
      aria-label={'Uputa: ' + text.title} aria-describedby={open ? popupId : undefined}
      aria-expanded={open} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
      onClick={() => setOpen(true)}>
      <Info aria-hidden="true" size={15} strokeWidth={1.7} />
    </button>
    {open && createPortal(
      <span className="hint-popover" ref={popup} role="tooltip" id={popupId} style={position}>
        <strong>{text.title}</strong>{text.body}
      </span>, document.body,
    )}
  </>
}
