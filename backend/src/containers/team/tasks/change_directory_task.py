from uuid import UUID

from fastapi import HTTPException

from src.containers.team.models.directory import TeamMember, User
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.containers.team.requests.directory_request import RenameUserRequest
from src.ship.auth import Actor


class ChangeDirectoryTask:
    async def rename(
        self, repo: DirectoryRepository, actor: Actor, user_id: UUID, request: RenameUserRequest
    ) -> User:
        actor.require_manager()
        user = await repo.user(user_id, actor.workspace.value, lock=True)
        if user is None:
            raise HTTPException(404, "Пользователь не найден")
        if user.version != request.version:
            raise HTTPException(409, "Имя уже изменено. Повторите действие.")
        user.name = request.name
        user.version += 1
        return user

    async def membership(
        self,
        repo: DirectoryRepository,
        actor: Actor,
        team_id: UUID,
        user_id: UUID,
        role: str | None = None,
        member_id: UUID | None = None,
    ) -> TeamMember | None:
        actor.require_manager()
        if await repo.team(team_id, actor.workspace.value) is None:
            raise HTTPException(404, "Бригада не найдена")
        if await repo.user(user_id, actor.workspace.value) is None:
            raise HTTPException(404, "Пользователь не найден")
        existing = await repo.member(team_id, user_id)
        if role is not None:
            if existing:
                raise HTTPException(409, "Пользователь уже состоит в бригаде")
            member = TeamMember(
                workspace_id=actor.workspace.value, team_id=team_id, user_id=user_id, role=role
            )
            await repo.add(member)
            return member
        if existing is None or existing.id != member_id:
            raise HTTPException(409, "Состав бригады уже изменён. Обновите список.")
        # Existing assignments remain as history; a removed member loses mutation rights.
        # Manager can reassign unfinished work to another current member.
        await repo.delete(existing)
        return None
