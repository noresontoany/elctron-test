import { shallowRef } from 'vue'
import { createTransaction } from '@tanstack/vue-db'
import { currentSession } from '@/entities/session'
import {
  getOrdersCollection,
  orderApi,
  orderMapper,
  lastTxid,
  type Order,
  type OrderForm,
  type OrderStatus,
} from '@/entities/order'

export function useOrderMutations() {
  const busy = shallowRef(false)
  const error = shallowRef('')
  const collection = getOrdersCollection()

  async function run(action: () => Promise<unknown>): Promise<boolean> {
    if (busy.value) return false
    busy.value = true
    error.value = ''
    try {
      await action()
      return true
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Не удалось сохранить заказ'
      return false
    } finally {
      busy.value = false
    }
  }
  const create = (form: OrderForm) =>
    run(async () => {
      const now = new Date().toISOString()
      await collection
        .insert({
          ...orderMapper.toCreate(crypto.randomUUID(), form),
          status: 'queued',
          version: 1,
          created_at: now,
          updated_at: now,
        })
        .when('settled')
    })
  const update = (order: Order, form: OrderForm) =>
    run(async () => {
      const { id: _, ...fields } = orderMapper.toCreate(order.id, form)
      // Protect stale editor drafts as well as concurrent requests.
      if (collection.get(order.id)?.version !== order.version) {
        throw new Error('Заказ изменён в другой вкладке. Закройте и откройте карточку заново.')
      }
      await collection
        .update(order.id, (draft) => {
          Object.assign(draft, fields)
        })
        .when('settled')
    })
  const move = (order: Order, status: OrderStatus) =>
    run(async () => {
      await collection
        .update(order.id, (draft) => {
          draft.status = status
        })
        .when('settled')
    })
  const remove = (order: Order) =>
    run(async () => {
      await collection.delete(order.id).when('settled')
    })
  const deliver = (order: Order) =>
    run(async () => {
      // Custom operation bypasses optimistic CRUD and enforces business rules on the API.
      const result = await orderApi.deliver(order.id, order.version)
      lastTxid.value = result.txid
      await collection.utils.awaitTxId(result.txid, 15000)
    })
  const claim = (order: Order) =>
    run(async () => {
      const transaction = createTransaction({
        mutationFn: async () => {
          const result = await orderApi.claim(order.id, order.version)
          lastTxid.value = result.txid
          await collection.utils.awaitTxId(result.txid, 15000)
        },
      })
      transaction.mutate(() =>
        collection.update(order.id, (draft) => {
          draft.status = 'repair'
          draft.assignee_id = currentSession.value!.user.id
        }),
      )
      await transaction.when('settled')
    })
  return { busy, error, create, update, move, remove, deliver, claim }
}
