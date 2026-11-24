import { shallowRef } from 'vue'
import { syncDiagnostics } from '@/shared/sync'
import { api } from '@/shared/api/client'

interface DemoUser {
  id: string
  name: string
  role: 'manager' | 'mechanic'
  version: number
}
interface DemoSession {
  token: string
  user: DemoUser
  users: DemoUser[]
  workspace: string
}
export const currentSession = shallowRef<DemoSession>()
export async function connectSession() {
  const requested = new URLSearchParams(window.location.search).get('workspace')
  if (
    (requested === 'lab' || requested === 'studio') &&
    sessionStorage.getItem('spoke.workspace') !== requested
  ) {
    sessionStorage.setItem('spoke.workspace', requested)
    sessionStorage.removeItem('spoke.user')
  }
  const session = await api<DemoSession>('/session', {
    method: 'POST',
    body: JSON.stringify({
      workspace: sessionStorage.getItem('spoke.workspace') || 'studio',
      user_id: sessionStorage.getItem('spoke.user') || undefined,
    }),
  })
  sessionStorage.setItem('spoke.token', session.token)
  currentSession.value = session
  Object.assign(window, { spokeSync: syncDiagnostics })
}
export function switchUser(userId: string) {
  sessionStorage.setItem('spoke.user', userId)
  // Dispose all live queries and reconnect every shape under the new identity.
  window.location.reload()
}
