import { chromium } from '@playwright/test'
import { parseArgs } from 'node:util'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'
import { randomUUID } from 'node:crypto'

const { values } = parseArgs({
  options: {
    url: { type: 'string', default: 'https://localhost:8447' },
    tabs: { type: 'string', default: '10' },
    writes: { type: 'string', default: '10' },
    mode: { type: 'string', default: 'shared' },
    output: { type: 'string', default: '../.artifacts/bench/tabs.json' },
    'local-tls': { type: 'boolean', default: false },
  },
})
const tabs = Number(values.tabs),
  writes = Number(values.writes)
if (
  !Number.isInteger(tabs) ||
  tabs < 1 ||
  !Number.isInteger(writes) ||
  writes < 1 ||
  !['shared', 'direct'].includes(values.mode)
)
  throw new Error('Expected --tabs >= 1 --writes >= 1 --mode shared|direct')
const browser = await chromium.launch({
  args: values['local-tls'] ? ['--ignore-certificate-errors'] : [],
  executablePath:
    process.env.CHROMIUM_PATH ||
    (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),
})
const context = await browser.newContext({
  baseURL: values.url,
  ignoreHTTPSErrors: values['local-tls'],
})
const pages = [],
  ids = [],
  protocols = new Set(),
  errors = [],
  timings = [],
  apiTimings = []
let auth
function summary(samples) {
  const sorted = [...samples].sort((a, b) => a - b)
  return Object.fromEntries(
    [50, 95, 99].map((p) => [
      `p${p}_ms`,
      Math.round(sorted[Math.ceil((sorted.length * p) / 100) - 1] ?? 0),
    ]),
  )
}
try {
  for (let i = 0; i < tabs; i++) {
    const page = await context.newPage()
    page.on('pageerror', (error) => errors.push(error.message))
    const cdp = await context.newCDPSession(page)
    await cdp.send('Network.enable')
    cdp.on('Network.responseReceived', (event) => protocols.add(event.response.protocol))
    await page.goto(`/?workspace=lab&sync=${values.mode === 'direct' ? 'direct' : 'shared'}`)
    await page.getByText('Синхронизировано', { exact: true }).waitFor()
    await page.locator('.order-card').first().waitFor()
    pages.push(page)
  }
  const diagnostics = await Promise.all(
    pages.map((page) => page.evaluate(() => window.spokeSync())),
  )
  const logical = diagnostics.reduce((sum, d) => sum + d.collections.length, 0)
  const unique =
    values.mode === 'direct'
      ? logical
      : new Set(diagnostics.flatMap((d) => d.collections.map((c) => `${c.scope}:${c.resource}`)))
          .size
  auth = {
    Authorization: `Bearer ${await pages[0].evaluate(() => sessionStorage.getItem('spoke.token'))}`,
  }
  for (let i = 0; i < writes; i++) {
    const id = randomUUID()
    ids.push(id)
    const started = performance.now()
    const response = await context.request.post('/api/orders', {
      headers: auth,
      data: {
        id,
        title: `Browser benchmark ${id.slice(0, 8)}`,
        bike: 'Browser Bench',
        customer_name: 'Browser Benchmark',
        estimate: 100,
      },
    })
    apiTimings.push(performance.now() - started)
    if (response.status() !== 201) throw new Error(`Write failed: ${response.status()}`)
    await Promise.all(
      pages.map(async (page) => {
        await page.locator(`[data-order-id="${id}"]`).waitFor({ state: 'attached', timeout: 15000 })
        timings.push(performance.now() - started)
      }),
    )
  }
  // Closing all but one must release their subscribers without stopping the remaining tab.
  await Promise.all(pages.slice(1).map((page) => page.close()))
  await pages[0].waitForFunction(async () =>
    (await window.spokeSync()).collections.every((c) => c.subscribers === 1),
  )
  const report = {
    tabs,
    writes,
    mode: values.mode,
    logicalSubscriptions: logical,
    electricCollections: unique,
    protocols: [...protocols],
    api: summary(apiTimings),
    writeToDom: summary(timings),
    deliveries: timings.length,
    errors,
    diagnostics: diagnostics[0],
    afterClosing: await pages[0].evaluate(() => window.spokeSync()),
    note: 'DOM measurement uses Playwright polling; not a precise paint timer. Same browser profile and user.',
  }
  mkdirSync(dirname(values.output), { recursive: true })
  writeFileSync(values.output, JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify(report, null, 2))
  if (errors.length) process.exitCode = 1
} finally {
  if (auth)
    for (const id of ids) {
      const response = await context.request.delete(`/api/orders/${id}`, {
        headers: auth,
        data: { version: 1 },
      })
      if (![200, 404].includes(response.status())) {
        console.error(`Cleanup failed ${id}: ${response.status()}`)
        process.exitCode = 1
      }
    }
  await browser.close()
}
