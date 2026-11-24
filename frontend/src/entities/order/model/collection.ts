import { createCollection } from '@tanstack/vue-db'
import { sharedElectricOptions } from '@/shared/sync'
import { shallowRef } from 'vue'
import { orderDtoSchema } from '../api/order.dto'
import { orderApi } from '../api/order.api'
import { orderMapper } from '../api/order.mapper'

export const syncError = shallowRef<string | null>(null)
export const syncConnected = shallowRef(false)
export const lastTxid = shallowRef<number | null>(null)

export function createOrdersCollection() {
  return createCollection(
    sharedElectricOptions({
      id: 'workshop-orders',
      schema: orderDtoSchema,
      getKey: (row) => row.id,
      syncMode: 'eager',
      resource: 'orders',
      onHealth: (connected, error) => {
        syncConnected.value = connected
        syncError.value = connected ? null : (error ?? 'Связь потеряна. Повторяем подключение…')
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
