import { test, expect, type Page } from '@playwright/test'

type Stats = {
  mode: string
  collections: { scope: string; resource: string; subscribers: number }[]
}
const stats = (page: Page) =>
  page.evaluate(() => (window as unknown as { spokeSync: () => Promise<Stats> }).spokeSync())
async function ready(page: Page, query = 'workspace=lab') {
  await page.goto(`/?${query}`)
  await expect(page.locator('.order-card').first()).toBeVisible()
  await expect.poll(async () => (await stats(page)).collections.length).toBe(4)
}

test('same identity shares four collections, late tabs hydrate and closing releases subscribers', async ({
  page,
  context,
}) => {
  await ready(page)
  const second = await context.newPage()
  await ready(second)
  const third = await context.newPage()
  await ready(third)
  await expect
    .poll(async () => (await stats(page)).collections.map((c) => c.subscribers))
    .toEqual([3, 3, 3, 3])
  expect((await stats(page)).mode).toBe('shared-worker')
  expect(await third.locator('.order-card').count()).toBe(await page.locator('.order-card').count())
  await second.close()
  await expect
    .poll(async () => (await stats(page)).collections.map((c) => c.subscribers))
    .toEqual([2, 2, 2, 2])
  await third.reload()
  await expect
    .poll(async () => (await stats(page)).collections.map((c) => c.subscribers))
    .toEqual([2, 2, 2, 2])
})

test('workspace and user changes create isolated subscriptions', async ({ page, context }) => {
  await ready(page)
  const other = await context.newPage()
  await ready(other, 'workspace=studio')
  const labScope = (await stats(page)).collections[0]!.scope
  expect((await stats(other)).collections[0]!.scope).not.toBe(labScope)
  await ready(other)
  await expect.poll(async () => (await stats(page)).collections[0]!.subscribers).toBe(2)
  const selector = other.getByLabel('Демо-пользователь · эта вкладка')
  const mechanic = await selector
    .locator('option')
    .filter({ hasText: 'Мария' })
    .getAttribute('value')
  await selector.selectOption(mechanic!)
  await expect.poll(async () => (await stats(page)).collections[0]!.subscribers).toBe(1)
  await expect.poll(async () => (await stats(other)).collections[0]?.scope).not.toBe(labScope)
  expect((await stats(other)).collections.every((c) => c.subscribers === 1)).toBeTruthy()
})

test('per-tab fallback uses the same official Electric adapter without sharing', async ({
  page,
  context,
}) => {
  await ready(page, 'workspace=lab&sync=direct')
  const other = await context.newPage()
  await ready(other, 'workspace=lab&sync=direct')
  for (const tab of [page, other]) {
    const result = await stats(tab)
    expect(result.mode).toBe('per-tab')
    expect(result.collections.every((c) => c.subscribers === 1)).toBeTruthy()
  }
})
