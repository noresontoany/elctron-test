import { z } from 'zod'

export const orderDtoSchema = z.object({
  id: z.uuid(),
  title: z.string(),
  bike: z.string(),
  customer_name: z.string(),
  description: z.string(),
  team_id: z.uuid(),
  assignee_id: z.uuid().nullable(),
  priority: z.enum(['normal', 'urgent']),
  status: z.enum(['queued', 'repair', 'ready', 'delivered']),
  estimate: z.number(),
  version: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type OrderDto = z.infer<typeof orderDtoSchema>
export type CreateOrderDto = Pick<
  OrderDto,
  | 'id'
  | 'title'
  | 'bike'
  | 'customer_name'
  | 'description'
  | 'team_id'
  | 'assignee_id'
  | 'priority'
  | 'estimate'
>
export type UpdateOrderDto = Partial<Omit<CreateOrderDto, 'id'>> & {
  version: number
  status?: OrderDto['status']
}
export interface MutationDto {
  txid: number
  order: OrderDto | null
}
