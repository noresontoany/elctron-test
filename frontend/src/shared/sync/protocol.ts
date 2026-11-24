export type Resource = 'orders' | 'users' | 'teams' | 'team_members'
export type Row = { id: string } & Record<string, unknown>
export type Change = { type: 'insert' | 'update' | 'delete'; value: Row }
export type ToWorker =
  | { type: 'connect'; resource: Resource; token: string }
  | { type: 'await'; id: number; txid: number; timeout: number }
  | { type: 'stats'; id: number }
  | { type: 'close' | 'pong' | 'ack' }
export type FromWorker =
  | { type: 'snapshot'; rows: Row[] }
  | { type: 'changes'; changes: Change[] }
  | { type: 'health'; connected: boolean }
  | { type: 'fatal'; error: string }
  | { type: 'reply'; id: number; value?: unknown; error?: string }
  | { type: 'ping' }
export interface SyncStats {
  resource: Resource
  subscribers: number
  rows: number
  requests: number
  activeRequests: number
  scope: string
}
