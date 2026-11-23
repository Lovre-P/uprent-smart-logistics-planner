import { expect, test, type Page } from '@playwright/test'

const summary = (page: Page) => page.getByRole('region', { name: 'Sažetak plana' })

async function applyHandlingLimit(page: Page) {
  await expect(summary(page).getByText('182,2 km', { exact: true })).toBeVisible()
  const calculate = page.getByRole('button', { name: 'Izračunaj drugo tumačenje', exact: true })
  const apply = page.getByRole('button', { name: 'Primijeni', exact: true })
  await expect(calculate.or(apply)).toBeVisible()
  if (await calculate.isVisible()) await calculate.click()
  await apply.click()
  await expect(summary(page).getByText('200,1 km', { exact: true })).toBeVisible()
  await expect(page.getByRole('switch', { name: 'U 9 h ulazi i utovar/istovar', exact: true })).toBeChecked()
}

test('loads default plan', async ({ page }) => {
  await page.goto('/')
  await expect(summary(page).getByText('182,2 km', { exact: true })).toBeVisible()
  await expect(summary(page).getByText('10/10', { exact: true })).toBeVisible()
  await expect(page.getByRole('banner').getByText(/^Dokazano optimalno/)).toBeVisible()
})

test('apply alternative reading', async ({ page }) => {
  await page.goto('/')
  await applyHandlingLimit(page)
})

test('kilometraža dionice i cijelog plana ima jednu decimalu', async ({ page }) => {
  await page.goto('/')
  await expect(summary(page)).toContainText('182,2 km')
  const steps = page.getByRole('table', { name: 'Koraci rute: Kamion B' })
  const legCells = steps.locator('tbody tr td:nth-child(5)')
  await expect.soft(legCells.filter({ hasText: /^17,0 km$/ }).first()).toBeVisible()
  await applyHandlingLimit(page)
  for (const name of ['Trajanje utovara', 'Trajanje istovara']) {
    const duration = page.getByRole('textbox', { name, exact: true })
    await duration.fill('21')
    await duration.press('Enter')
  }
  await expect(summary(page).getByText('217,0 km', { exact: true })).toBeVisible()
})

test('heavy order warning', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('tab', { name: 'Ulazni podaci' }).click()
  await page.getByRole('button', { name: 'Dodaj stroj', exact: true }).click()
  const machine = page.getByRole('form', { name: 'Uređivanje: Strojevi' })
  await machine.getByLabel('Oznaka', { exact: true }).fill('M11')
  await machine.getByLabel('Masa (kg)', { exact: true }).fill('12000')
  await machine.getByRole('button', { name: 'Spremi stroj' }).click()
  await expect(page.getByRole('table', { name: 'Strojevi' }).getByRole('rowheader', { name: 'M11' })).toBeVisible()

  await page.getByRole('button', { name: 'Dodaj nalog', exact: true }).click()
  const order = page.getByRole('form', { name: 'Uređivanje: Transportni nalozi' })
  await order.getByLabel('Oznaka', { exact: true }).fill('N11')
  await order.getByLabel('Stroj', { exact: true }).fill('M11')
  await order.getByLabel('Preuzimanje', { exact: true }).fill('L1')
  await order.getByLabel('Isporuka', { exact: true }).fill('L3')
  await order.getByRole('button', { name: 'Spremi nalog' }).click()
  await expect(page.getByRole('table', { name: 'Transportni nalozi' }).getByRole('rowheader', { name: 'N11' })).toBeVisible()

  await page.getByRole('tab', { name: 'Plan', exact: true }).click()
  await expect(summary(page).getByText('10/11', { exact: true })).toBeVisible()
  const warnings = page.getByRole('region', { name: 'Neizvršeni nalozi' })
  await expect(warnings.getByRole('button', { name: 'Otvori nalog N11' })).toBeVisible()
  await expect(warnings.getByText('TOO_HEAVY', { exact: true })).toBeVisible()
  await expect(warnings).toContainText('M11 teži 12.000 kg')
})

test('prikvačeni raspored s krivulje ima objašnjenje i povratak na optimum', async ({ page }) => {
  await page.goto('/')
  await expect(summary(page)).toContainText('182,2 km')
  await page.getByRole('tab', { name: 'Analiza' }).click()
  await page.getByRole('button', { name: 'Prikaži raspored: 284,2 km, 344,8 min' }).click()
  await expect(summary(page)).toContainText('284,2 km')
  const banner = page.getByRole('region', { name: 'Prikvačeni nalozi' })
  await expect(banner).toContainText(/Prikazan je raspored uz prikvačene naloge \(.*N03 → A.*\)\. Optimalan je uz ta prikvačivanja\./)
  await expect(page.getByRole('banner')).toContainText('Optimalno uz prikvačene naloge')
  await page.getByRole('tab', { name: 'Analiza' }).click()
  await expect(banner).toContainText('N03 → A')
  await banner.getByRole('button', { name: 'Vrati optimalni plan' }).click()
  await expect(summary(page)).toContainText('182,2 km')
  await expect(banner).toHaveCount(0)
  await expect(page.getByRole('banner')).toContainText('Dokazano optimalno')
})

test('hint explains limit', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Uputa: U 9 h ulazi i utovar/istovar' }).click()
  await expect(page.getByRole('tooltip')).toContainText('vozač može voziti 9 h')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('tooltip')).toBeHidden()
})

test('reset', async ({ page }) => {
  await page.goto('/')
  await applyHandlingLimit(page)
  await page.getByRole('button', { name: 'Pomoć', exact: true }).click()
  await page.getByRole('button', { name: 'Vrati podatke i postavke iz zadatka' }).click()
  await expect(summary(page).getByText('182,2 km', { exact: true })).toBeVisible()
  await expect(page.getByRole('switch', { name: 'U 9 h ulazi i utovar/istovar', exact: true })).not.toBeChecked()
})

test('mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(summary(page).getByText('182,2 km', { exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  const settings = page.getByRole('button', { name: 'Postavke', exact: true })
  await expect(settings).toBeVisible()
  await settings.click()
  await expect(page.getByRole('dialog', { name: 'Postavke' })).toBeVisible()
  await page.getByRole('button', { name: 'Zatvori postavke' }).click()
  await expect(page.getByRole('dialog', { name: 'Postavke' })).toBeHidden()
})
