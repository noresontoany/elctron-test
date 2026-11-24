from pydantic import BaseModel

from src.containers.order.resources.order_resource import OrderResource


class MutationResource(BaseModel):
    txid: int
    order: OrderResource | None
