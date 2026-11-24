import { createCollection } from '@tanstack/vue-db'
import { electricCollectionOptions } from '@tanstack/electric-db-collection'
import { shallowRef } from 'vue'
import { authenticatedFetch } from '@/shared/api/auth'
import { orderDtoSchema } from '../api/order.dto'
import { orderApi } from '../api/order.api'
import { orderMapper } from '../api/order.mapper'

export const syncError = shallowRef<string | null>(null)
export const syncConnected = shallowRef(false)
export const lastTxid = shallowRef<number | null>(null)

export function createOrdersCollection() {
  return createCollection(
    electricCollectionOptions({
      id: 'workshop-orders',
      schema: orderDtoSchema,
      getKey: (row) => row.id,
      syncMode: 'eager',
      shapeOptions: {
        url: new URL('/api/sync/orders', window.location.origin).href,
        fetchClient: async (input, init) => {
          try {
            const response = await authenticatedFetch(input, init)
            if (response.ok) {
              syncConnected.value = true
              syncError.value = null
            } else if (response.status !== 409) {
              syncConnected.value = false
              syncError.value = 'Синхронизация временно недоступна'
            }
            return response
          } catch (error) {
            if (!(error instanceof DOMException && error.name === 'AbortError')) {
              syncConnected.value = false
              syncError.value = 'Связь потеряна. Повторяем подключение…'
            }
            throw error
          }
        },
        onError: () => {
          syncConnected.value = false
          syncError.value = 'Связь потеряна. Повторяем подключение…'
          return {}
        },
      },
      onInsert: async ({ transaction, collection }) => {
        for (const mutation of transaction.mutations) {
          const row = mutation.modified
          const result = await orderApi.create(
            orderMapper.toCreate(row.id, orderMapper.toModel(row)),
          )
          lastTxid.value = result.txid
          await collection.utils.awaitTxId(result.txid, 15000)
        }
      },
      onUpdate: async ({ transaction, collection }) => {
        for (const mutation of transaction.mutations) {
          const result = await orderApi.update(
            mutation.original.id,
            orderMapper.toUpdate(mutation.changes, mutation.original.version),
          )
          lastTxid.value = result.txid
          await collection.utils.awaitTxId(result.txid, 15000)
        }
      },
      onDelete: async ({ transaction, collection }) => {
        for (const mutation of transaction.mutations) {
          const result = await orderApi.delete(mutation.original.id, mutation.original.version)
          lastTxid.value = result.txid
          await collection.utils.awaitTxId(result.txid, 15000)
        }
      },
    }),
  )
}
export type OrdersCollection = ReturnType<typeof createOrdersCollection>
let collection: OrdersCollection | undefined
export function getOrdersCollection(): OrdersCollection {
  return (collection ??= createOrdersCollection())
}
