from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from src.containers.session.requests.demo_session_request import DemoSessionRequest
from src.containers.team.repositories.directory_repository import DirectoryRepository
from src.containers.team.resources.directory_resource import UserResource
from src.ship.auth import COOKIE, signer
from src.ship.database import session_factory
from src.ship.demo_ids import demo_id

router = APIRouter(tags=["Demo session"])


class SessionResource(BaseModel):
    workspace: str
    token: str
    user: UserResource
    users: list[UserResource]
    demo: bool = True


@router.post("/session", response_model=SessionResource)
async def demo_session(body: DemoSessionRequest, response: Response):
    """Public local demo login. Replace with real authentication before deployment."""
    async with session_factory() as session:
        repo = DirectoryRepository(session)
        user_id = body.user_id or demo_id(body.workspace.value, "user", "Ирина")
        user = await repo.user(user_id, body.workspace.value)
        if user is None:
            raise HTTPException(404, "Пользователь не найден в этой мастерской")
        users = await repo.users(body.workspace.value)
        token = signer().dumps({"workspace": body.workspace.value, "user_id": str(user.id)})
        response.set_cookie(
            COOKIE, token, httponly=True, samesite="strict", max_age=86400, path="/api"
        )
        return SessionResource(
            workspace=body.workspace.value,
            token=token,
            user=UserResource.from_model(user),
            users=[UserResource.from_model(row) for row in users],
        )
