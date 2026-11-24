import { api } from '@/shared/api/client'
import type { CreateOrderDto, UpdateOrderDto, MutationDto } from './order.dto'

export const orderApi = {
  create: (body: CreateOrderDto) =>
    api<MutationDto>('/orders', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: UpdateOrderDto) =>
    api<MutationDto>(`/orders/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (id: string, version: number) =>
    api<MutationDto>(`/orders/${id}`, { method: 'DELETE', body: JSON.stringify({ version }) }),
  claim: (id: string, version: number) =>
    api<MutationDto>(`/orders/${id}/claim`, { method: 'POST', body: JSON.stringify({ version }) }),
  deliver: (id: string, version: number) =>
    api<MutationDto>(`/orders/${id}/deliver`, {
      method: 'POST',
      body: JSON.stringify({ version }),
    }),
}
