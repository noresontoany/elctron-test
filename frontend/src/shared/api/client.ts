import { authHeaders } from './auth'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...options.headers },
  })
  const body = await response.json()
  if (!response.ok) {
    const message =
      typeof body.detail === 'string'
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((item: { msg: string }) => item.msg).join('; ')
          : 'Не удалось выполнить запрос'
    throw new ApiError(response.status, message)
  }
  return body as T
}
