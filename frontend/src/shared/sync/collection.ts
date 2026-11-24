import type { CollectionConfig } from '@tanstack/db'
import type { z } from 'zod'
import type { FromWorker, Resource, SyncStats, ToWorker } from './protocol'

type Utils = { awaitTxId: (txid: number, timeout?: number) => Promise<boolean> }
type Config<T extends { id: string }> = Omit<
  CollectionConfig<T, string, z.ZodType<T>, Utils>,
  'sync' | 'utils'
> & {
  resource: Resource
  schema: z.ZodType<T>
  onHealth?: (connected: boolean, error?: string) => void
}
let sharedMode: boolean | undefined
let dedicatedWorker: Worker | undefined
const diagnostics = new Map<Resource, () => Promise<SyncStats>>()
export async function syncDiagnostics() {
  return {
    mode: useSharedWorker() ? 'shared-worker' : 'per-tab',
    collections: await Promise.all([...diagnostics.values()].map((read) => read())),
  }
}
function useSharedWorker() {
  return (sharedMode ??=
    typeof SharedWorker !== 'undefined' &&
    new URLSearchParams(location.search).get('sync') !== 'direct')
}
export function sharedElectricOptions<T extends { id: string }>(
  config: Config<T>,
): CollectionConfig<T, string, z.ZodType<T>, Utils> & { utils: Utils; schema: z.ZodType<T> } {
  const { resource, onHealth, ...base } = config
  let port: MessagePort | undefined
  let nextId = 0
  const pending = new Map<
    number,
    {
      resolve: (value: unknown) => void
      reject: (error: Error) => void
      timer: ReturnType<typeof setTimeout>
    }
  >()
  const send = (message: ToWorker) => port?.postMessage(message)
  const rpc = (
    message: { type: 'stats' } | { type: 'await'; txid: number; timeout: number },
    timeout = 15000,
  ) =>
    new Promise<unknown>((resolve, reject) => {
      const id = ++nextId
      const timer = setTimeout(() => {
        pending.delete(id)
        reject(new Error('Истекло время ожидания синхронизации'))
      }, timeout + 1000)
      pending.set(id, { resolve, reject, timer })
      send({ ...message, id })
    })
  return {
    ...base,
    utils: {
      awaitTxId: async (txid, timeout = 15000) => {
        await rpc({ type: 'await', txid, timeout }, timeout)
        return true
      },
    },
    sync: {
      sync: ({ begin, write, commit, markReady, fail }) => {
        let worker: SharedWorker | Worker
        if (useSharedWorker()) {
          const shared = new SharedWorker(new URL('./sync.worker.ts', import.meta.url), {
            type: 'module',
            name: 'spoke-sync-v1',
          })
          worker = shared
          port = shared.port
        } else {
          dedicatedWorker ??= new Worker(new URL('./sync.worker.ts', import.meta.url), {
            type: 'module',
          })
          worker = dedicatedWorker
          const channel = new MessageChannel()
          port = channel.port1
          worker.postMessage(null, [channel.port2])
        }
        let ready = false
        const stopPending = (error: Error) => {
          for (const waiter of pending.values()) {
            clearTimeout(waiter.timer)
            waiter.reject(error)
          }
          pending.clear()
        }
        const fatal = (error: Error) => {
          onHealth?.(false, error.message)
          stopPending(error)
          send({ type: 'close' })
          port?.close()
          fail(error)
        }
        const workerError = () => fatal(new Error('Worker остановлен. Обновите страницу.'))
        worker.addEventListener('error', workerError)
        port.onmessage = ({ data }: MessageEvent<FromWorker>) => {
          try {
            if (data.type === 'snapshot') {
              begin({ snapshot: true })
              for (const row of data.rows)
                write({ type: 'insert', value: config.schema.parse(row) })
              commit()
              ready = true
              markReady()
              send({ type: 'ack' })
            } else if (data.type === 'changes' && ready) {
              begin()
              for (const change of data.changes)
                write({ type: change.type, value: config.schema.parse(change.value) })
              // Don't await this receipt: optimistic writes settle only AFTER awaitTxId.
              commit()
              send({ type: 'ack' })
            } else if (data.type === 'health') onHealth?.(data.connected)
            else if (data.type === 'fatal') fatal(new Error(data.error))
            else if (data.type === 'ping') send({ type: 'pong' })
            else if (data.type === 'reply') {
              const waiter = pending.get(data.id)
              if (waiter) {
                clearTimeout(waiter.timer)
                pending.delete(data.id)
                if (data.error) waiter.reject(new Error(data.error))
                else waiter.resolve(data.value)
              }
            }
          } catch (error) {
            fatal(error instanceof Error ? error : new Error(String(error)))
          }
        }
        port.start()
        send({ type: 'connect', resource, token: sessionStorage.getItem('spoke.token') || '' })
        diagnostics.set(resource, () => rpc({ type: 'stats' }) as Promise<SyncStats>)
        const close = () => {
          send({ type: 'close' })
          port?.close()
          stopPending(new Error('Подписка закрыта'))
        }
        const restore = (event: PageTransitionEvent) => {
          if (event.persisted) location.reload()
        }
        window.addEventListener('pagehide', close)
        window.addEventListener('pageshow', restore)
        return () => {
          close()
          worker.removeEventListener('error', workerError)
          diagnostics.delete(resource)
          window.removeEventListener('pagehide', close)
          window.removeEventListener('pageshow', restore)
        }
      },
    },
  }
}
