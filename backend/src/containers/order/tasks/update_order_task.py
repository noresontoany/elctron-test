from datetime import UTC, datetime

from fastapi import HTTPException

from src.containers.order.models.order import Order
from src.containers.order.requests.update_order_request import UpdateOrderRequest


class UpdateOrderTask:
    async def run(self, order: Order, request: UpdateOrderRequest) -> Order:
        if order.status == "delivered":
            raise HTTPException(409, "Выданный заказ доступен только для чтения")
        if request.status == "delivered":
            raise HTTPException(409, "Для выдачи используйте отдельную операцию")
        transitions = {"queued": {"repair"}, "repair": {"queued", "ready"}, "ready": {"repair"}}
        if request.status and request.status != order.status:
            if request.status not in transitions[order.status]:
                raise HTTPException(409, "Сначала возьмите заказ в работу")
        for field, value in request.model_dump(exclude_unset=True, exclude={"version"}).items():
            setattr(order, field, value)
        order.version += 1
        order.updated_at = datetime.now(UTC)
        return order
