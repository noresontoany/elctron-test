import { z } from 'zod'
export const userSchema = z.object({
  id: z.uuid(),
  name: z.string(),
  role: z.enum(['manager', 'mechanic']),
  version: z.number(),
})
export const teamSchema = z.object({ id: z.uuid(), name: z.string() })
export const memberSchema = z.object({
  id: z.uuid(),
  team_id: z.uuid(),
  user_id: z.uuid(),
  role: z.enum(['lead', 'mechanic']),
})
export type UserDto = z.infer<typeof userSchema>
export type TeamDto = z.infer<typeof teamSchema>
export type MemberDto = z.infer<typeof memberSchema>
