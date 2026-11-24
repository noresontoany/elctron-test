// sessionStorage isolates demo identities between tabs, unlike a shared cookie.
export function authHeaders(): Record<string, string> {
  const token = sessionStorage.getItem('spoke.token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}
export const authenticatedFetch: typeof fetch = (input, init) => {
  const headers = new Headers(init?.headers)
  for (const [key, value] of Object.entries(authHeaders())) headers.set(key, value)
  return fetch(input, { ...init, headers })
}
