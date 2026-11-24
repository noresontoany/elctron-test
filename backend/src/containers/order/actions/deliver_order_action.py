from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.version_request import VersionRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.containers.order.resources.order_resource import OrderResource
from src.containers.order.tasks.authorize_order_task import AuthorizeOrderTask
from src.containers.order.tasks.deliver_order_task import DeliverOrderTask
from src.containers.order.tasks.lock_order_task import LockOrderTask
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor
from src.ship.tasks.transaction_id_task import TransactionIdTask


class DeliverOrderAction:
    async def run(
        self, session: AsyncSession, request: VersionRequest, actor: Actor, order_id: UUID
    ) -> MutationResource:
        workspace = actor.workspace
        async with session.begin():
            repository = OrderRepository(session)
            order = await LockOrderTask().run(repository, order_id, workspace, request.version)
            await AuthorizeOrderTask().edit(DirectoryRepository(session), actor, order)
            order = await DeliverOrderTask().run(order)
            txid = await TransactionIdTask().run(repository)
            resource = OrderResource.from_model(order)
        # The context has committed before the txid leaves the API.
        return MutationResource(txid=txid, order=resource)
