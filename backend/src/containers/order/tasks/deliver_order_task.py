from datetime import UTC, datetime

from fastapi import HTTPException

from src.containers.order.models.order import Order


class DeliverOrderTask:
    async def run(self, order: Order) -> Order:
        if order.status != "ready":
            raise HTTPException(409, "Можно выдать только готовый велосипед")
        order.status = "delivered"
        order.version += 1
        order.updated_at = datetime.now(UTC)
        return order
