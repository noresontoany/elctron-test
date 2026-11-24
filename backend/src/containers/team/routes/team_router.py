from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.team.actions.change_directory_action import ChangeDirectoryAction
from src.containers.team.requests.directory_request import AddMemberRequest, RenameUserRequest
from src.containers.team.resources.directory_resource import DirectoryMutationResource
from src.ship.auth import Actor, get_actor
from src.ship.database import get_session

router = APIRouter(tags=["Team"])
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentActor = Annotated[Actor, Depends(get_actor)]


@router.patch("/users/{user_id}", response_model=DirectoryMutationResource)
async def rename_user(
    user_id: UUID, body: RenameUserRequest, session: Session, actor: CurrentActor
):
    return await ChangeDirectoryAction().rename(session, actor, user_id, body)


@router.post("/teams/{team_id}/members", response_model=DirectoryMutationResource, status_code=201)
async def add_member(team_id: UUID, body: AddMemberRequest, session: Session, actor: CurrentActor):
    return await ChangeDirectoryAction().membership(
        session, actor, team_id, body.user_id, body.role
    )


@router.delete(
    "/teams/{team_id}/members/{user_id}/{member_id}", response_model=DirectoryMutationResource
)
async def remove_member(
    team_id: UUID, user_id: UUID, member_id: UUID, session: Session, actor: CurrentActor
):
    return await ChangeDirectoryAction().membership(
        session, actor, team_id, user_id, member_id=member_id
    )
