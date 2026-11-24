import { test, expect, type Page } from '@playwright/test'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'

const createdIds: string[] = []
test.afterAll(() => {
  execFileSync('python', ['../scripts/cleanup_test_orders.py'], {
    input: JSON.stringify(createdIds),
  })
})

async function ready(page: Page) {
  await page.goto('/')
  await expect(page.getByText('Синхронизировано', { exact: true })).toBeVisible()
  await expect(page.locator('.loading-card')).toHaveCount(0)
}
async function seed(page: Page, title: string) {
  const id = randomUUID()
  const response = await page.request.post('/api/orders', {
    data: {
      id,
      title,
      bike: 'E2E Bike',
      customer_name: 'E2E Test',
      estimate: 2400,
    },
  })
  expect(response.status()).toBe(201)
  createdIds.push(id)
  return id
}

test('CRUD, two-tab sync, status changes and custom delivery', async ({ page, context }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await ready(page)
  const other = await context.newPage()
  await ready(other)
  const title = `E2E Ремонт ${Date.now()}`
  await page.getByRole('button', { name: 'Новый заказ', exact: true }).first().click()
  await page.getByLabel('Что нужно сделать').fill(title)
  await page.getByLabel('Велосипед', { exact: true }).fill('E2E Trek')
  await page.getByLabel('Клиент', { exact: true }).fill('E2E Test')
  await page.getByLabel('Стоимость, ₽').fill('3200')
  const createdResponse = page.waitForResponse(
    (response) => response.url().endsWith('/api/orders') && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Создать заказ', exact: true }).click()
  createdIds.push((await (await createdResponse).json()).order.id)
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await expect(other.getByRole('button', { name: title, exact: true })).toBeVisible()
  await page.getByRole('button', { name: title, exact: true }).click()
  await page.getByLabel('Комментарий мастеру').fill('Проверить тормоза')
  await page.getByRole('button', { name: 'Сохранить', exact: true }).click()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  const card = page.locator('.order-card').filter({ hasText: title })
  const otherCard = other.locator('.order-card').filter({ hasText: title })
  await expect(otherCard).toContainText('Проверить тормоза')
  await card.getByRole('button', { name: 'Взять в работу' }).click()
  await expect(other.locator('.repair')).toContainText(title)
  await expect(card.getByRole('button', { name: 'Завершить ремонт' })).toBeEnabled()
  await card.getByRole('button', { name: 'Завершить ремонт' }).click()
  await expect(other.locator('.ready')).toContainText(title)
  await expect(card.getByRole('button', { name: 'Выдать велосипед' })).toBeEnabled()
  await card.getByRole('button', { name: 'Выдать велосипед' }).click()
  await expect(otherCard).toHaveCount(0)
  await page.getByRole('link', { name: 'Архив заказов' }).click()
  await expect(page.locator('tr').filter({ hasText: title })).toContainText('E2E Trek')
  await page.reload()
  await expect(page.locator('tr').filter({ hasText: title })).toBeVisible()
  expect(errors).toEqual([])
})

test('optimistic UI before API reply; failed write rolls back', async ({ page }) => {
  await ready(page)
  const title = `E2E Откат ${Date.now()}`
  const id = await seed(page, title)
  const card = page.locator(`[data-order-id="${id}"]`)
  await expect(card).toBeVisible()
  let reject!: () => void
  const held = new Promise<void>((resolve) => {
    reject = resolve
  })
  await page.route(`**/api/orders/${id}`, async (route) => {
    if (route.request().method() !== 'PATCH') return route.continue()
    await held
    await route.fulfill({
      status: 409,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Тестовый конфликт версии' }),
    })
  })
  await card.getByRole('button', { name: 'Взять в работу' }).click()
  await expect(page.locator('.repair')).toContainText(title)
  reject()
  await expect(page.getByRole('alert')).toContainText('Тестовый конфликт версии')
  await expect(page.locator('.queued')).toContainText(title)
  await page.unroute(`**/api/orders/${id}`)
  await page.request.delete(`/api/orders/${id}`, { data: { version: 1 } })
})

test('delete and search with no page reload', async ({ page, context }) => {
  await ready(page)
  const other = await context.newPage()
  await ready(other)
  const title = `E2E Удаление ${Date.now()}`
  const id = await seed(page, title)
  await expect(other.locator(`[data-order-id="${id}"]`)).toBeVisible()
  await page.getByLabel('Поиск заказов').fill(title)
  await expect(page.locator('.order-card')).toHaveCount(1)
  await page.getByRole('button', { name: title, exact: true }).click()
  await page.getByRole('button', { name: 'Удалить заказ', exact: true }).click()
  await page.getByRole('button', { name: 'Да, удалить', exact: true }).click()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await expect(other.locator(`[data-order-id="${id}"]`)).toHaveCount(0)
})

test('desktop and mobile layout, architecture and Swagger', async ({ page }) => {
  await ready(page)
  const id = await seed(page, `E2E Адаптивность ${Date.now()}`)
  await expect(page.locator(`[data-order-id="${id}"]`)).toBeVisible()
  await expect(page.locator('.new-order-button')).toHaveCSS('display', /^(inline-)?flex$/)
  await page.screenshot({ path: '../.artifacts/desktop.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.getByRole('link', { name: 'Как это устроено' }).click()
  await expect(page.getByRole('heading', { name: /Простой интерфейс/ })).toBeVisible()
  await expect(page.locator('.diagram-node')).toHaveCount(5)
  expect((await page.request.get('/api/openapi.json')).ok()).toBeTruthy()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.locator('.order-card').first()).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.screenshot({ path: '../.artifacts/mobile.png', fullPage: true })
  await page.getByRole('button', { name: 'Новый заказ', exact: true }).first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByRole('dialog')).toHaveCSS('position', 'fixed')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
})

test('stale editor cannot overwrite another tab', async ({ page, context }) => {
  await ready(page)
  const title = `E2E Черновик ${Date.now()}`
  const id = await seed(page, title)
  const other = await context.newPage()
  await ready(other)
  await page.getByRole('button', { name: title, exact: true }).click()
  await page.getByLabel('Комментарий мастеру').fill('Устаревший черновик')
  const response = await other.request.patch(`/api/orders/${id}`, {
    data: { version: 1, description: 'Свежий комментарий из другой вкладки' },
  })
  expect(response.ok()).toBeTruthy()
  await expect(page.locator(`[data-order-id="${id}"]`)).toContainText('Свежий комментарий')
  await page.getByRole('button', { name: 'Сохранить', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Заказ изменён в другой вкладке')
  await expect(other.locator(`[data-order-id="${id}"]`)).toContainText('Свежий комментарий')
})

test('sync reconnects after a browser network interruption', async ({ page, context }) => {
  await ready(page)
  await context.setOffline(true)
  await expect(page.getByText('Нет связи', { exact: true })).toBeVisible()
  await context.setOffline(false)
  const title = `E2E Переподключение ${Date.now()}`
  const id = await seed(page, title)
  await expect(page.locator(`[data-order-id="${id}"]`)).toBeVisible()
  await expect(page.getByText('Синхронизировано', { exact: true })).toBeVisible()
})
