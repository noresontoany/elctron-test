from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.containers.team.requests.directory_request import RenameUserRequest
from src.containers.team.resources.directory_resource import (
    DirectoryMutationResource,
    MemberResource,
    UserResource,
)
from src.containers.team.tasks.change_directory_task import ChangeDirectoryTask
from src.ship.auth import Actor
from src.ship.repositories.transaction_repository import TransactionRepository
from src.ship.tasks.transaction_id_task import TransactionIdTask


class ChangeDirectoryAction:
    async def rename(
        self, session: AsyncSession, actor: Actor, user_id: UUID, request: RenameUserRequest
    ) -> DirectoryMutationResource:
        async with session.begin():
            user = await ChangeDirectoryTask().rename(
                DirectoryRepository(session), actor, user_id, request
            )
            txid = await TransactionIdTask().run(TransactionRepository(session))
            result = DirectoryMutationResource(txid=txid, user=UserResource.from_model(user))
        return result

    async def membership(
        self,
        session: AsyncSession,
        actor: Actor,
        team_id: UUID,
        user_id: UUID,
        role: str | None = None,
        member_id: UUID | None = None,
    ) -> DirectoryMutationResource:
        async with session.begin():
            member = await ChangeDirectoryTask().membership(
                DirectoryRepository(session), actor, team_id, user_id, role, member_id
            )
            txid = await TransactionIdTask().run(TransactionRepository(session))
            result = DirectoryMutationResource(
                txid=txid, member=MemberResource.from_model(member) if member else None
            )
        return result
