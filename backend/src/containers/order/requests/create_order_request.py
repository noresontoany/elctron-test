from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.containers.order.enums.order_priority import OrderPriority


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: UUID
    title: str = Field(min_length=3, max_length=120)
    bike: str = Field(min_length=2, max_length=100)
    customer_name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=2000)
    team_id: UUID | None = None
    assignee_id: UUID | None = None
    priority: OrderPriority = OrderPriority.NORMAL
    estimate: int = Field(default=0, ge=0, le=1000000, strict=True)
