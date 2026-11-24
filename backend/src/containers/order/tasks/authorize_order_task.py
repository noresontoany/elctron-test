from fastapi import HTTPException

from src.containers.order.models.order import Order
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.auth import Actor


class AuthorizeOrderTask:
    async def assignment(self, repo: DirectoryRepository, actor: Actor, team_id, assignee_id):
        if await repo.team(team_id, actor.workspace.value) is None:
            raise HTTPException(404, "Бригада не найдена")
        if assignee_id is not None and await repo.member(team_id, assignee_id) is None:
            raise HTTPException(409, "Мастер должен состоять в выбранной бригаде")

    async def edit(self, repo: DirectoryRepository, actor: Actor, order: Order):
        if actor.role == "manager":
            return
        if (
            order.assignee_id != actor.user_id
            or await repo.member(order.team_id, actor.user_id) is None
        ):
            raise HTTPException(
                403, "Изменять заказ может назначенный мастер своей бригады или руководитель"
            )
