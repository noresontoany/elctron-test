import { createCollection } from '@tanstack/db'
import { electricCollectionOptions } from '@tanstack/electric-db-collection'
import type { FromWorker, Resource, Row, ToWorker } from './protocol'

// Only this worker owns Electric connections. The official adapter handles log resets,
// transaction evidence and retry semantics; tabs mirror its committed collection.
const entries = new Map<string, Entry>()
const clients = new Set<Client>()
interface Client {
  port: MessagePort
  token: string
  scope: string
  lastSeen: number
  connecting?: Promise<void>
  entry?: Entry
  closed: boolean
  ready: boolean
  pending: number
}
const send = (client: Client, message: FromWorker) => {
  if (client.closed) return
  if (message.type === 'changes' || message.type === 'snapshot') {
    if (++client.pending > 256) {
      fatal(client, new Error('Вкладка не успевает принимать данные. Обновите страницу.'))
      return
    }
  }
  client.port.postMessage(message)
}
class SessionError extends Error {}
async function verify(token: string) {
  const response = await fetch('/api/session', {
    headers: { Authorization: `Bearer ${token}` },
    credentials: 'omit',
    signal: AbortSignal.timeout(10000),
  })
  if (response.status === 401 || response.status === 403)
    throw new SessionError('Сессия истекла. Обновите страницу.')
  if (!response.ok) throw new Error('Сервер сессий временно недоступен')
  const actor = await response.json()
  return `${actor.workspace}:${actor.user_id}:${actor.role}`
}
function makeEntry(resource: Resource, scope: string, token: string) {
  const state = { token, requests: 0, activeRequests: 0, connected: false }
  const subscribers = new Set<Client>()
  const health = (connected: boolean) => {
    state.connected = connected
    for (const client of subscribers) send(client, { type: 'health', connected })
  }
  const collection = createCollection(
    electricCollectionOptions<Row>({
      id: `${scope}:${resource}`,
      getKey: (row) => row.id,
      syncMode: 'eager',
      shapeOptions: {
        url: new URL(`/api/sync/${resource}`, location.origin).href,
        fetchClient: async (input, init) => {
          state.requests++
          state.activeRequests++
          try {
            const headers = new Headers(init?.headers)
            headers.set('Authorization', `Bearer ${state.token}`)
            const response = await fetch(input, { ...init, headers, credentials: 'omit' })
            health(response.ok)
            return response
          } catch (error) {
            health(false)
            throw error
          } finally {
            state.activeRequests--
          }
        },
        onError: () => {
          health(false)
          return {}
        },
      },
    }),
  )
  const subscription = collection.subscribeChanges((changes) => {
    const batch = changes.map(({ type, value }) => ({ type, value: { ...value } }))
    for (const client of subscribers) {
      if (!client.ready) continue
      send(client, {
        type: 'changes',
        changes: batch,
      })
    }
  })
  return { resource, scope, state, subscribers, collection, subscription }
}
type Entry = ReturnType<typeof makeEntry>
function close(client: Client) {
  if (client.closed) return
  client.closed = true
  clients.delete(client)
  client.port.close()
  const entry = client.entry
  if (!entry) return
  entry.subscribers.delete(client)
  if (!entry.subscribers.size) {
    entries.delete(`${entry.scope}:${entry.resource}`)
    entry.subscription.unsubscribe()
    void entry.collection.cleanup()
  }
}
function fatal(client: Client, error: unknown) {
  send(client, {
    type: 'fatal',
    error: error instanceof Error ? error.message : 'Ошибка синхронизации',
  })
  close(client)
}
async function connect(client: Client, resource: Resource, token: string) {
  if (client.scope || !['orders', 'users', 'teams', 'team_members'].includes(resource))
    throw new Error('Недопустимая подписка')
  client.scope = 'pending'
  const scope = await verify(token)
  if (client.closed) return
  client.token = token
  client.scope = scope
  const key = `${scope}:${resource}`
  let entry = entries.get(key)
  if (!entry) {
    entry = makeEntry(resource, scope, token)
    entries.set(key, entry)
  }
  entry.state.token = token
  client.entry = entry
  // Retain during initial loading; changes aren't forwarded until the snapshot below.
  entry.subscribers.add(client)
  await entry.collection.preload()
  if (client.closed) return
  send(client, {
    type: 'snapshot',
    rows: [...entry.collection.values()].map((row) => ({ ...row })),
  })
  client.ready = true
  send(client, { type: 'health', connected: entry.state.connected })
}

// No Window globals: SharedWorker works for all same-origin tabs, including background tabs.
const worker = globalThis as unknown as {
  onconnect: (event: MessageEvent) => void
  onmessage: (event: MessageEvent) => void
}
worker.onconnect = (event) => {
  const port = event.ports[0]!
  const client: Client = {
    port,
    token: '',
    scope: '',
    lastSeen: Date.now(),
    closed: false,
    ready: false,
    pending: 0,
  }
  clients.add(client)
  port.onmessage = async ({ data }: MessageEvent<ToWorker>) => {
    client.lastSeen = Date.now()
    try {
      if (data.type === 'connect') {
        client.connecting = connect(client, data.resource, data.token)
        await client.connecting
      } else if (data.type === 'close') close(client)
      else if (data.type === 'ack') client.pending = Math.max(0, client.pending - 1)
      else if (data.type === 'await') {
        await client.connecting
        if (client.closed || !client.entry) return
        try {
          await client.entry.collection.utils.awaitTxId(data.txid, Math.min(data.timeout, 30000))
          // FIFO MessagePort ordering: committed changes precede this confirmation.
          send(client, { type: 'reply', id: data.id })
        } catch (error) {
          send(client, { type: 'reply', id: data.id, error: String(error) })
        }
      } else if (data.type === 'stats') {
        await client.connecting
        if (client.closed || !client.entry) return
        const { resource, scope, state, subscribers, collection } = client.entry
        send(client, {
          type: 'reply',
          id: data.id,
          value: {
            resource,
            scope,
            subscribers: subscribers.size,
            rows: collection.size,
            requests: state.requests,
            activeRequests: state.activeRequests,
          },
        })
      }
    } catch (error) {
      fatal(client, error)
    }
  }
  port.start()
}
worker.onmessage = worker.onconnect
// Reclaim ports after crashed/frozen tabs; ordinary pagehide closes immediately.
setInterval(() => {
  for (const client of clients) {
    if (Date.now() - client.lastSeen > 120000)
      fatal(client, new Error('Вкладка была приостановлена. Обновите страницу.'))
    else send(client, { type: 'ping' })
  }
}, 15000)
// Revalidate each token (not just the most recently connected user's token).
let validating = false
setInterval(async () => {
  if (validating) return
  validating = true
  try {
    const verified = new Map<string, Promise<string>>()
    await Promise.all(
      [...clients]
        .filter((client) => client.token)
        .map(async (client) => {
          let result = verified.get(client.token)
          if (!result) {
            result = verify(client.token)
            verified.set(client.token, result)
          }
          try {
            if ((await result) !== client.scope)
              throw new SessionError('Права изменились. Обновите страницу.')
          } catch (error) {
            if (error instanceof SessionError) fatal(client, error)
            else send(client, { type: 'health', connected: false })
          }
        }),
    )
  } finally {
    validating = false
  }
}, 60000)
