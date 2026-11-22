import { expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { hints } from '../content/hints'
import { SETTINGS_KEYS } from '../types'
import { Hint } from './Hint'

it('svaka postavka objašnjava svoj učinak', () => {
  for (const key of SETTINGS_KEYS) {
    expect(hints.settings[key].title.length).toBeGreaterThan(0)
    expect(hints.settings[key].body.length).toBeGreaterThan(0)
  }
  for (const text of ['voziti', '182,2 km', '200,1 km']) {
    expect(hints.settings.limit_includes_handling.body).toContain(text)
  }
})
it('oblačić se otvara klikom i zatvara tipkom Escape', async () => {
  const user = userEvent.setup()
  render(<Hint id="limit_includes_handling" />)
  expect(screen.queryByRole('tooltip')).toBeNull()
  await user.click(screen.getByRole('button'))
  expect(screen.getByRole('tooltip').textContent).toContain('voziti')
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('tooltip')).toBeNull()
  expect(document.activeElement).toBe(screen.getByRole('button'))
})
it('oblačić podržava fokus i klik izvan njega', async () => {
  const user = userEvent.setup()
  render(<><Hint id="load_min" /><button>Sljedeće</button></>)
  await user.tab()
  expect(screen.getByRole('tooltip').textContent).toContain('20 min')
  await user.click(screen.getByRole('button', { name: 'Sljedeće' }))
  expect(screen.queryByRole('tooltip')).toBeNull()
})
