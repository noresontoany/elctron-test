from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.models.order import Order
from src.ship.repositories.transaction_repository import TransactionRepository
from src.ship.workspace import Workspace


class OrderRepository(TransactionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_for_update(self, order_id: UUID, workspace: Workspace) -> Order | None:
        query = (
            select(Order)
            .where(
                Order.id == order_id,
                Order.workspace_id == workspace.value,
            )
            .with_for_update()
        )
        return await self.session.scalar(query)

    async def add(self, order: Order) -> None:
        self.session.add(order)
        await self.session.flush()

    async def delete(self, order: Order) -> None:
        await self.session.delete(order)
