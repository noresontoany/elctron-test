import { createCollection } from '@tanstack/vue-db'
import { sharedElectricOptions } from '@/shared/sync'
import { userSchema, teamSchema, memberSchema } from '../api/directory.dto'

function createDirectory() {
  return {
    users: createCollection(
      sharedElectricOptions({
        id: 'users',
        schema: userSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        resource: 'users',
      }),
    ),
    teams: createCollection(
      sharedElectricOptions({
        id: 'teams',
        schema: teamSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        resource: 'teams',
      }),
    ),
    members: createCollection(
      sharedElectricOptions({
        id: 'team-members',
        schema: memberSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        resource: 'team_members',
      }),
    ),
  }
}
let directory: ReturnType<typeof createDirectory> | undefined
export const getDirectory = () => (directory ??= createDirectory())
