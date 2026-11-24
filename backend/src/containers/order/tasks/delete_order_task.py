from fastapi import HTTPException

from src.containers.order.models.order import Order
from src.containers.order.repositories.order_repository import OrderRepository


class DeleteOrderTask:
    async def run(self, repository: OrderRepository, order: Order) -> None:
        if order.status != "queued":
            raise HTTPException(409, "Удалить можно только заказ из очереди")
        await repository.delete(order)
