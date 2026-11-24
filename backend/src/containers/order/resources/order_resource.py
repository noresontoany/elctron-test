from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.containers.order.enums.order_priority import OrderPriority
from src.containers.order.enums.order_status import OrderStatus
from src.containers.order.models.order import Order


class OrderResource(BaseModel):
    id: UUID
    title: str
    bike: str
    customer_name: str
    description: str
    team_id: UUID
    assignee_id: UUID | None
    priority: OrderPriority
    status: OrderStatus
    estimate: int
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, order: Order) -> "OrderResource":
        # Explicit public projection: workspace and future private columns stay server-side.
        return cls(
            id=order.id,
            title=order.title,
            bike=order.bike,
            customer_name=order.customer_name,
            description=order.description,
            team_id=order.team_id,
            assignee_id=order.assignee_id,
            priority=OrderPriority(order.priority),
            status=OrderStatus(order.status),
            estimate=order.estimate,
            version=order.version,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
