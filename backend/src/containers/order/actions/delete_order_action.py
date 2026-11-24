from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.version_request import VersionRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.containers.order.tasks.delete_order_task import DeleteOrderTask
from src.containers.order.tasks.lock_order_task import LockOrderTask
from src.ship.auth import Actor
from src.ship.tasks.transaction_id_task import TransactionIdTask


class DeleteOrderAction:
    async def run(
        self, session: AsyncSession, request: VersionRequest, actor: Actor, order_id: UUID
    ) -> MutationResource:
        actor.require_manager()
        workspace = actor.workspace
        async with session.begin():
            repository = OrderRepository(session)
            order = await LockOrderTask().run(repository, order_id, workspace, request.version)
            await DeleteOrderTask().run(repository, order)
            txid = await TransactionIdTask().run(repository)
            resource = None
        # The context has committed before the txid leaves the API.
        return MutationResource(txid=txid, order=resource)
