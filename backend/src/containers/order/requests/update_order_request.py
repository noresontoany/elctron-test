from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.containers.order.enums.order_priority import OrderPriority
from src.containers.order.enums.order_status import OrderStatus


class UpdateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    version: int = Field(ge=1, strict=True)
    title: str | None = Field(default=None, min_length=3, max_length=120)
    bike: str | None = Field(default=None, min_length=2, max_length=100)
    customer_name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    team_id: UUID | None = None
    assignee_id: UUID | None = None
    priority: OrderPriority | None = None
    status: OrderStatus | None = None
    estimate: int | None = Field(default=None, ge=0, le=1000000, strict=True)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "UpdateOrderRequest":
        if any(getattr(self, key) is None for key in self.model_fields_set - {"assignee_id"}):
            raise ValueError("Переданные поля не могут быть null")
        if self.model_fields_set == {"version"}:
            raise ValueError("Укажите хотя бы одно поле для изменения")
        return self
