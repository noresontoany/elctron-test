from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.create_order_request import CreateOrderRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.containers.order.resources.order_resource import OrderResource
from src.containers.order.tasks.authorize_order_task import AuthorizeOrderTask
from src.containers.order.tasks.create_order_task import CreateOrderTask
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor
from src.ship.tasks.transaction_id_task import TransactionIdTask


class CreateOrderAction:
    async def run(
        self, session: AsyncSession, request: CreateOrderRequest, actor: Actor
    ) -> MutationResource:
        actor.require_manager()
        workspace = actor.workspace
        async with session.begin():
            repository = OrderRepository(session)
            order = await CreateOrderTask().run(repository, request, workspace)
            await AuthorizeOrderTask().assignment(
                DirectoryRepository(session), actor, order.team_id, order.assignee_id
            )
            txid = await TransactionIdTask().run(repository)
            resource = OrderResource.from_model(order)
        # The context has committed before the txid leaves the API.
        return MutationResource(txid=txid, order=resource)
