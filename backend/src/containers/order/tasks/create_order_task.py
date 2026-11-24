from src.containers.order.models.order import Order
from src.containers.order.repositories.order_repository import OrderRepository
from src.containers.order.requests.create_order_request import CreateOrderRequest
from src.ship.demo_ids import demo_id
from src.ship.workspace import Workspace


class CreateOrderTask:
    async def run(
        self, repository: OrderRepository, request: CreateOrderRequest, workspace: Workspace
    ) -> Order:
        order = Order(
            id=request.id,
            workspace_id=workspace.value,
            title=request.title,
            bike=request.bike,
            customer_name=request.customer_name,
            description=request.description,
            team_id=request.team_id or demo_id(workspace.value, "team", "service"),
            assignee_id=request.assignee_id,
            priority=request.priority.value,
            estimate=request.estimate,
        )
        await repository.add(order)
        return order
