from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.ship.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        ForeignKeyConstraint(
            ["team_id", "workspace_id"], ["teams.id", "teams.workspace_id"], name="fk_order_team"
        ),
        ForeignKeyConstraint(
            ["assignee_id", "workspace_id"],
            ["users.id", "users.workspace_id"],
            name="fk_order_assignee",
        ),
        CheckConstraint("status IN ('queued','repair','ready','delivered')", name="order_status"),
        CheckConstraint("priority IN ('normal','urgent')", name="order_priority"),
        CheckConstraint("estimate >= 0 AND estimate <= 1000000", name="order_estimate"),
        CheckConstraint("version >= 1", name="order_version"),
        CheckConstraint("workspace_id IN ('studio','lab')", name="order_workspace"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(120))
    bike: Mapped[str] = mapped_column(String(100))
    customer_name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    team_id: Mapped[UUID] = mapped_column(index=True)
    assignee_id: Mapped[UUID | None] = mapped_column(index=True)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="queued")
    estimate: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
