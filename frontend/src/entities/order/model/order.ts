export type OrderStatus = 'queued' | 'repair' | 'ready' | 'delivered'
export type OrderPriority = 'normal' | 'urgent'

export interface Order {
  id: string
  title: string
  bike: string
  customerName: string
  description: string
  teamId: string
  assigneeId: string | null
  priority: OrderPriority
  status: OrderStatus
  estimate: number
  version: number
  createdAt: Date
  updatedAt: Date
}
export interface OrderForm {
  title: string
  bike: string
  customerName: string
  description: string
  teamId: string
  assigneeId: string | null
  priority: OrderPriority
  estimate: number
}
export const statusLabels: Record<OrderStatus, string> = {
  queued: 'В очереди',
  repair: 'В работе',
  ready: 'Готово к выдаче',
  delivered: 'Выдано',
}
export interface OrderView extends Order {
  assignee: string
  teamName: string
}
export const money = (value: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(value)
export const shortId = (id: string) => `SP-${id.slice(0, 4).toUpperCase()}`
