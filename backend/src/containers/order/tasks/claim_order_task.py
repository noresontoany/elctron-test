from datetime import UTC, datetime

from fastapi import HTTPException

from src.containers.order.models.order import Order
from src.containers.order.tasks.authorize_order_task import AuthorizeOrderTask
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor


class ClaimOrderTask:
    async def run(self, directory: DirectoryRepository, actor: Actor, order: Order) -> None:
        await AuthorizeOrderTask().assignment(directory, actor, order.team_id, actor.user_id)
        if order.status != "queued" or order.assignee_id not in (None, actor.user_id):
            raise HTTPException(409, "Заказ уже взят другим мастером или вышел из очереди")
        order.assignee_id = actor.user_id
        order.status = "repair"
        order.version += 1
        order.updated_at = datetime.now(UTC)
