import { test, expect, type Page, type APIRequestContext } from '@playwright/test'
import { randomUUID } from 'node:crypto'
import { execFileSync } from 'node:child_process'

const createdIds: string[] = []
test.afterAll(() => {
  execFileSync('python', ['../scripts/cleanup_test_orders.py'], {
    input: JSON.stringify(createdIds),
  })
})
async function ready(page: Page, path = '/') {
  await page.goto(`${path}?workspace=lab`)
  await expect(page.getByText('Синхронизировано', { exact: true })).toBeVisible()
  await expect(page.getByLabel('Демо-пользователь · эта вкладка').locator('option')).toHaveCount(4)
}
async function headers(page: Page) {
  return {
    Authorization: `Bearer ${await page.evaluate(() => sessionStorage.getItem('spoke.token'))}`,
  }
}
async function shape(request: APIRequestContext, resource: string, auth: Record<string, string>) {
  const rows = new Map<string, Record<string, string>>()
  let params: Record<string, string> = { offset: '-1' }
  for (let i = 0; i < 100; i++) {
    const result = await request.get(`/api/sync/${resource}`, { headers: auth, params })
    expect(result.ok()).toBeTruthy()
    for (const message of await result.json()) {
      if (message.value) {
        const id = message.value.id
        if (message.headers.operation === 'delete') rows.delete(id)
        else rows.set(id, { ...rows.get(id), ...message.value })
      }
      if (message.headers.control === 'up-to-date') return [...rows.values()]
    }
    params = {
      offset: result.headers()['electric-offset']!,
      handle: result.headers()['electric-handle']!,
    }
  }
  throw new Error('Electric snapshot did not complete')
}

async function seed(page: Page, auth: Record<string, string>, teamId: string) {
  const id = randomUUID()
  const response = await page.request.post('/api/orders', {
    headers: auth,
    data: {
      id,
      title: `E2E Связи ${id.slice(0, 8)}`,
      bike: 'E2E Bike',
      customer_name: 'E2E Test',
      team_id: teamId,
      estimate: 2400,
      priority: 'urgent',
    },
  })
  expect(response.status()).toBe(201)
  createdIds.push(id)
  return id
}

test('membership join, tab identity, claim, aggregation and rename propagate independently', async ({
  page,
  context,
}) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await ready(page, '/team')
  const auth = await headers(page)
  const users = await shape(page.request, 'users', auth)
  const maria = users.find((row) => row.name === 'Мария')!
  const service = (await shape(page.request, 'teams', auth)).find(
    (row) => row.name === 'Сервис и ТО',
  )!
  const original = (await shape(page.request, 'team_members', auth)).find(
    (row) => row.team_id === service.id && row.user_id === maria.id,
  )
  const memberPath = `/api/teams/${service.id}/members`
  if (original)
    expect(
      (
        await page.request.delete(`${memberPath}/${maria.id}/${original.id}`, { headers: auth })
      ).ok(),
    ).toBeTruthy()
  const orderId = await seed(page, auth, service.id!)
  const other = await context.newPage()
  other.on('pageerror', (error) => errors.push(error.message))
  let addedId: string | undefined
  let renamed = false
  const changedName = `Мария E2E ${Date.now()}`
  try {
    await ready(other)
    await other.getByLabel('Демо-пользователь · эта вкладка').selectOption(maria.id!)
    await expect(other.getByRole('button', { name: /Моя очередь/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await expect(other.getByLabel('Демо-пользователь · эта вкладка')).toHaveValue(maria.id!)
    const otherCard = other.locator(`[data-order-id="${orderId}"]`)
    await expect(otherCard).toHaveCount(0)
    // Shared cookie changed to Maria, manager's tab still holds its own bearer token.
    await expect(page.getByLabel('Демо-пользователь · эта вкладка')).not.toHaveValue(maria.id!)
    const teamCard = page.locator(`[data-team-id="${service.id}"]`)
    await teamCard.getByLabel('Добавить в Сервис и ТО', { exact: true }).selectOption(maria.id!)
    const addedResponse = page.waitForResponse(
      (r) => r.url().endsWith(memberPath) && r.request().method() === 'POST',
    )
    await teamCard.getByRole('button', { name: 'Добавить участника: Сервис и ТО' }).click()
    const addition = await addedResponse
    expect(addition.status()).toBe(201)
    addedId = (await addition.json()).member.id
    await expect(otherCard).toBeVisible()
    // No order write is needed to make it enter the query result.
    let persisted = (await shape(page.request, 'orders', auth)).find((row) => row.id === orderId)!
    expect(Number(persisted.version)).toBe(1)
    const workload = page.locator(`[data-user-id="${maria.id}"]`)
    const before = Number(await workload.getByTestId('workload-count').innerText())
    await otherCard.getByRole('button', { name: 'Взять в работу' }).click()
    await expect(otherCard.getByRole('button', { name: 'Завершить ремонт' })).toBeEnabled()
    await expect(workload.getByTestId('workload-count')).toHaveText(String(before + 1))
    await page.getByRole('button', { name: 'Переименовать Мария', exact: true }).click()
    await page.getByLabel('Новое имя: Мария', { exact: true }).fill(changedName)
    await workload.getByRole('button', { name: 'Сохранить', exact: true }).click()
    await expect(otherCard).toContainText(changedName)
    renamed = true
    persisted = (await shape(page.request, 'orders', auth)).find((row) => row.id === orderId)!
    expect(Number(persisted.version)).toBe(2)
    expect(persisted.assignee_id).toBe(maria.id)
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.screenshot({ path: '../.artifacts/team-desktop.png', fullPage: true })
    await page.setViewportSize({ width: 390, height: 844 })
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy()
    await expect(page.getByLabel('Демо-пользователь · эта вкладка')).toBeVisible()
    await page.screenshot({ path: '../.artifacts/team-mobile.png', fullPage: true })
    await teamCard
      .getByRole('button', { name: `Убрать ${changedName} из Сервис и ТО`, exact: true })
      .click()
    await expect(otherCard).toHaveCount(0)
    const denied = await other.request.patch(`/api/orders/${orderId}`, {
      headers: await headers(other),
      data: { version: 2, status: 'ready' },
    })
    expect(denied.status()).toBe(403)
    await other.getByRole('button', { name: 'Все заказы', exact: true }).click()
    await expect(otherCard).toBeVisible()
    await expect(otherCard.getByRole('button', { name: 'Завершить ремонт' })).toBeDisabled()
    expect(errors).toEqual([])
  } finally {
    if (addedId)
      await page.request.delete(`${memberPath}/${maria.id}/${addedId}`, { headers: auth })
    if (original)
      expect(
        (
          await page.request.post(memberPath, {
            headers: auth,
            data: { user_id: maria.id, role: original.role },
          })
        ).ok(),
      ).toBeTruthy()
    if (renamed) {
      const current = (await shape(page.request, 'users', auth)).find((row) => row.id === maria.id)!
      expect(
        (
          await page.request.patch(`/api/users/${maria.id}`, {
            headers: auth,
            data: { name: maria.name, version: Number(current.version) },
          })
        ).ok(),
      ).toBeTruthy()
    }
    await other.close()
  }
})

test('a rejected optimistic claim restores both status and assignee', async ({ page }) => {
  await ready(page)
  const auth = await headers(page)
  const users = await shape(page.request, 'users', auth)
  const alex = users.find((row) => row.name === 'Алексей')!
  const service = (await shape(page.request, 'teams', auth)).find(
    (row) => row.name === 'Сервис и ТО',
  )!
  const id = await seed(page, auth, service.id!)
  await page.getByLabel('Демо-пользователь · эта вкладка').selectOption(alex.id!)
  const card = page.locator(`[data-order-id="${id}"]`)
  await expect(card.getByRole('button', { name: 'Взять в работу' })).toBeEnabled()
  let reject!: () => void
  const held = new Promise<void>((resolve) => {
    reject = resolve
  })
  await page.route(`**/api/orders/${id}/claim`, async (route) => {
    await held
    await route.fulfill({
      status: 409,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Тестовый конфликт взятия' }),
    })
  })
  await card.getByRole('button', { name: 'Взять в работу' }).click()
  await expect(page.locator(`.repair [data-order-id="${id}"]`)).toBeVisible()
  await expect(card).toContainText('Алексей')
  reject()
  await expect(page.getByRole('alert')).toContainText('Тестовый конфликт взятия')
  await expect(page.locator(`.queued [data-order-id="${id}"]`)).toBeVisible()
  await expect(card).toContainText('Не назначен')
})
