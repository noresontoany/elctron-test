import { shallowRef } from 'vue'
import { api } from '@/shared/api/client'
import { getDirectory, type UserDto } from '@/entities/workforce'

export function useTeamMutations() {
  const busy = shallowRef(false)
  const error = shallowRef('')
  const { users, members } = getDirectory()
  async function run(action: () => Promise<void>) {
    if (busy.value) return false
    busy.value = true
    error.value = ''
    try {
      await action()
      return true
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Не удалось сохранить'
      return false
    } finally {
      busy.value = false
    }
  }
  const rename = (user: UserDto, name: string) =>
    run(async () => {
      const result = await api<{ txid: number }>(`/users/${user.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ name, version: user.version }),
      })
      await users.utils.awaitTxId(result.txid, 15000)
    })
  const add = (teamId: string, userId: string, role: string) =>
    run(async () => {
      const result = await api<{ txid: number }>(`/teams/${teamId}/members`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, role }),
      })
      await members.utils.awaitTxId(result.txid, 15000)
    })
  const remove = (teamId: string, userId: string, memberId: string) =>
    run(async () => {
      const result = await api<{ txid: number }>(`/teams/${teamId}/members/${userId}/${memberId}`, {
        method: 'DELETE',
      })
      await members.utils.awaitTxId(result.txid, 15000)
    })
  return { busy, error, rename, add, remove }
}
