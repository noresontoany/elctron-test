import { computed } from 'vue'
import { useLiveQuery, eq } from '@tanstack/vue-db'
import { getDirectory } from './collections'

export function useDirectory() {
  const collections = getDirectory()
  const usersQuery = useLiveQuery((q) =>
    q.from({ user: collections.users }).orderBy(({ user }) => user.name),
  )
  const teamsQuery = useLiveQuery((q) =>
    q.from({ team: collections.teams }).orderBy(({ team }) => team.name),
  )
  const membersQuery = useLiveQuery((q) =>
    q
      .from({ member: collections.members })
      .innerJoin({ user: collections.users }, ({ member, user }) => eq(member.user_id, user.id))
      .select(({ member, user }) => ({
        id: member.id,
        teamId: member.team_id,
        userId: member.user_id,
        role: member.role,
        name: user.name,
      })),
  )
  return {
    users: usersQuery.data,
    teams: teamsQuery.data,
    members: membersQuery.data,
    isLoading: computed(
      () =>
        usersQuery.isLoading.value || teamsQuery.isLoading.value || membersQuery.isLoading.value,
    ),
  }
}
