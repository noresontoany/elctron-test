import { createCollection } from '@tanstack/vue-db'
import { electricCollectionOptions } from '@tanstack/electric-db-collection'
import { authenticatedFetch } from '@/shared/api/auth'
import { userSchema, teamSchema, memberSchema } from '../api/directory.dto'

const shape = (resource: string) => ({
  url: new URL(`/api/sync/${resource}`, window.location.origin).href,
  fetchClient: authenticatedFetch,
})
function createDirectory() {
  return {
    users: createCollection(
      electricCollectionOptions({
        id: 'users',
        schema: userSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        shapeOptions: shape('users'),
      }),
    ),
    teams: createCollection(
      electricCollectionOptions({
        id: 'teams',
        schema: teamSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        shapeOptions: shape('teams'),
      }),
    ),
    members: createCollection(
      electricCollectionOptions({
        id: 'team-members',
        schema: memberSchema,
        getKey: (row) => row.id,
        syncMode: 'eager',
        shapeOptions: shape('team_members'),
      }),
    ),
  }
}
let directory: ReturnType<typeof createDirectory> | undefined
export const getDirectory = () => (directory ??= createDirectory())
