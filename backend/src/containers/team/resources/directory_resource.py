from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.containers.team.models.directory import Team, TeamMember, User


class UserResource(BaseModel):
    id: UUID
    name: str
    role: Literal["manager", "mechanic"]
    version: int

    @classmethod
    def from_model(cls, row: User):
        return cls(id=row.id, name=row.name, role=row.role, version=row.version)


class TeamResource(BaseModel):
    id: UUID
    name: str

    @classmethod
    def from_model(cls, row: Team):
        return cls(id=row.id, name=row.name)


class MemberResource(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    role: Literal["lead", "mechanic"]

    @classmethod
    def from_model(cls, row: TeamMember):
        return cls(id=row.id, team_id=row.team_id, user_id=row.user_id, role=row.role)


class DirectoryMutationResource(BaseModel):
    txid: int
    user: UserResource | None = None
    member: MemberResource | None = None
