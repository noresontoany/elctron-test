from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.version_request import VersionRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.containers.order.resources.order_resource import OrderResource
from src.containers.order.tasks.claim_order_task import ClaimOrderTask
from src.containers.order.tasks.lock_order_task import LockOrderTask
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor
from src.ship.tasks.transaction_id_task import TransactionIdTask


class ClaimOrderAction:
    async def run(
        self, session: AsyncSession, request: VersionRequest, actor: Actor, order_id: UUID
    ):
        async with session.begin():
            repo = OrderRepository(session)
            order = await LockOrderTask().run(repo, order_id, actor.workspace, request.version)
            directory = DirectoryRepository(session)
            await ClaimOrderTask().run(directory, actor, order)
            txid = await TransactionIdTask().run(repo)
            resource = OrderResource.from_model(order)
        return MutationResource(txid=txid, order=resource)
