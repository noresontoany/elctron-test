import { computed } from 'vue'
import { useLiveQuery, eq, not, count, sum } from '@tanstack/vue-db'
import { getOrdersCollection, orderMapper, type OrderView } from '@/entities/order'
import { getDirectory } from '@/entities/workforce'
import { currentSession } from '@/entities/session'

export function useWorkshopData() {
  const orders = getOrdersCollection()
  const { users, teams, members } = getDirectory()
  const userId = currentSession.value!.user.id
  const allQuery = useLiveQuery((q) =>
    q
      .from({ order: orders })
      .leftJoin({ user: users }, ({ order, user }) => eq(order.assignee_id, user.id))
      .innerJoin({ team: teams }, ({ order, team }) => eq(order.team_id, team.id))
      .orderBy(({ order }) => order.created_at, 'desc')
      .select(({ order, user, team }) => ({
        ...order,
        assignee_name: user?.name,
        team_name: team.name,
      })),
  )
  // Membership is an actual live join: deleting/inserting a link changes the result
  // without updating any order, invalidating a fetch or rebuilding a server DTO.
  const mineQuery = useLiveQuery((q) =>
    q
      .from({ order: orders })
      .innerJoin({ member: members }, ({ order, member }) => eq(order.team_id, member.team_id))
      .where(({ member }) => eq(member.user_id, userId))
      .leftJoin({ user: users }, ({ order, user }) => eq(order.assignee_id, user.id))
      .innerJoin({ team: teams }, ({ order, team }) => eq(order.team_id, team.id))
      .orderBy(({ order }) => order.created_at, 'desc')
      .select(({ order, user, team }) => ({
        ...order,
        assignee_name: user?.name,
        team_name: team.name,
      })),
  )
  const workloadQuery = useLiveQuery((q) =>
    q
      .from({ order: orders })
      .where(({ order }) => not(eq(order.status, 'delivered')))
      .groupBy(({ order }) => [order.assignee_id, order.priority])
      .select(({ order }) => ({
        userId: order.assignee_id,
        priority: order.priority,
        total: count(order.id),
        amount: sum(order.estimate),
      })),
  )
  type Joined = (typeof allQuery.data.value)[number]
  const project = (row: Joined): OrderView => ({
    ...orderMapper.toModel(row),
    assignee: row.assignee_name ?? 'Не назначен',
    teamName: row.team_name,
  })
  return {
    orders: computed(() => allQuery.data.value.map(project)),
    myOrders: computed(() => mineQuery.data.value.map(project)),
    workload: workloadQuery.data,
    isLoading: computed(() => allQuery.isLoading.value || mineQuery.isLoading.value),
  }
}
