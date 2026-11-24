from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.update_order_request import UpdateOrderRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.containers.order.resources.order_resource import OrderResource
from src.containers.order.tasks.authorize_order_task import AuthorizeOrderTask
from src.containers.order.tasks.lock_order_task import LockOrderTask
from src.containers.order.tasks.update_order_task import UpdateOrderTask
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor
from src.ship.tasks.transaction_id_task import TransactionIdTask


class UpdateOrderAction:
    async def run(
        self,
        session: AsyncSession,
        request: UpdateOrderRequest,
        actor: Actor,
        order_id: UUID,
    ) -> MutationResource:
        workspace = actor.workspace
        async with session.begin():
            repository = OrderRepository(session)
            order = await LockOrderTask().run(repository, order_id, workspace, request.version)
            directory = DirectoryRepository(session)
            policy = AuthorizeOrderTask()
            await policy.edit(directory, actor, order)
            if {"team_id", "assignee_id"} & request.model_fields_set:
                actor.require_manager()
                await policy.assignment(
                    directory,
                    actor,
                    request.team_id or order.team_id,
                    request.assignee_id
                    if "assignee_id" in request.model_fields_set
                    else order.assignee_id,
                )
            order = await UpdateOrderTask().run(order, request)
            txid = await TransactionIdTask().run(repository)
            resource = OrderResource.from_model(order)
        # The context has committed before the txid leaves the API.
        return MutationResource(txid=txid, order=resource)
