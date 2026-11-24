from uuid import UUID

from fastapi import HTTPException

from src.containers.order.models.order import Order
from src.containers.order.repositories.order_repository import OrderRepository
from src.ship.workspace import Workspace


class LockOrderTask:
    async def run(
        self, repository: OrderRepository, order_id: UUID, workspace: Workspace, version: int
    ) -> Order:
        order = await repository.find_for_update(order_id, workspace)
        if order is None:
            raise HTTPException(404, "Заказ не найден")
        if order.version != version:
            raise HTTPException(409, "Заказ уже изменён в другой вкладке. Повторите действие.")
        return order
