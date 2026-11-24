from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.ship.config import get_settings
from src.ship.database import session_factory
from src.ship.workspace import Workspace

COOKIE = "spoke_session"


def signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="spoke-session")


@dataclass(frozen=True)
class Actor:
    workspace: Workspace
    user_id: UUID
    role: str

    def require_manager(self):
        if self.role != "manager":
            raise HTTPException(403, "Это действие доступно руководителю")


async def get_actor(request: Request) -> Actor:
    header = request.headers.get("authorization")
    token = header.removeprefix("Bearer ") if header else request.cookies.get(COOKIE, "")
    try:
        payload = signer().loads(token, max_age=86400)
        workspace = Workspace(payload["workspace"])
        user_id = UUID(payload["user_id"])
    except (BadSignature, SignatureExpired, ValueError, KeyError, TypeError):
        raise HTTPException(401, "Демо-сессия истекла. Обновите страницу.") from None
    async with session_factory() as session:
        user = await DirectoryRepository(session).user(user_id, workspace.value)
        if user is None:
            raise HTTPException(401, "Пользователь не найден")
        return Actor(workspace, user.id, user.role)
