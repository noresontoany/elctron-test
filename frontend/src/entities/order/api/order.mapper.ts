import type { CreateOrderDto, OrderDto, UpdateOrderDto } from './order.dto'
import type { Order, OrderForm } from '../model/order'

export const orderMapper = {
  toModel(dto: OrderDto): Order {
    return {
      id: dto.id,
      title: dto.title,
      bike: dto.bike,
      customerName: dto.customer_name,
      description: dto.description,
      teamId: dto.team_id,
      assigneeId: dto.assignee_id,
      priority: dto.priority,
      status: dto.status,
      estimate: dto.estimate,
      version: dto.version,
      createdAt: new Date(dto.created_at),
      updatedAt: new Date(dto.updated_at),
    }
  },
  toCreate(id: string, form: OrderForm): CreateOrderDto {
    return {
      id,
      title: form.title.trim(),
      bike: form.bike.trim(),
      customer_name: form.customerName.trim(),
      description: form.description.trim(),
      team_id: form.teamId,
      assignee_id: form.assigneeId,
      priority: form.priority,
      estimate: form.estimate,
    }
  },
  toUpdate(changes: Partial<OrderDto>, version: number): UpdateOrderDto {
    // Whitelist writable fields; never send timestamps, IDs or workspace metadata.
    const dto: UpdateOrderDto = { version }
    for (const key of [
      'title',
      'bike',
      'customer_name',
      'description',
      'team_id',
      'assignee_id',
      'priority',
      'status',
      'estimate',
    ] as const) {
      if (changes[key] !== undefined) Object.assign(dto, { [key]: changes[key] })
    }
    return dto
  },
}
