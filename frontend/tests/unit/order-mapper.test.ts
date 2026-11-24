import { describe, it, expect } from 'vitest'
import { orderMapper } from '../../src/entities/order/api/order.mapper'
import type { OrderDto } from '../../src/entities/order/api/order.dto'

const dto: OrderDto = {
  id: '00000000-0000-4000-8000-000000000001',
  title: 'ТО велосипеда',
  bike: 'Trek',
  customer_name: 'Анна',
  description: '',
  team_id: '00000000-0000-4000-8000-000000000002',
  assignee_id: null,
  estimate: 1000,
  priority: 'normal',
  status: 'queued',
  version: 1,
  created_at: '2026-11-24 06:54:49.637065+00',
  updated_at: '2026-11-24 06:54:49.637065+00',
}
describe('order boundary mapping', () => {
  it('maps snake_case and PostgreSQL timestamps into a domain model', () => {
    const model = orderMapper.toModel(dto)
    expect(model.customerName).toBe('Анна')
    expect(model.createdAt.toISOString()).toBe('2026-11-24T06:54:49.637Z')
    expect(model).not.toHaveProperty('customer_name')
  })
  it('whitelists patch fields and preserves zero/empty values', () => {
    expect(
      orderMapper.toUpdate(
        {
          id: dto.id,
          created_at: 'untrusted',
          version: 100,
          estimate: 0,
          assignee_id: null,
          description: '',
        },
        2,
      ),
    ).toEqual({ version: 2, estimate: 0, assignee_id: null, description: '' })
  })
})
