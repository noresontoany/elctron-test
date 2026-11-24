from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.team.models.directory import Team, TeamMember, User


class DirectoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def user(self, user_id: UUID, workspace: str, *, lock=False):
        query = select(User).where(User.id == user_id, User.workspace_id == workspace)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def users(self, workspace: str):
        return (
            await self.session.scalars(
                select(User).where(User.workspace_id == workspace).order_by(User.name)
            )
        ).all()

    async def team(self, team_id: UUID, workspace: str):
        # Serializes membership changes and assignment validation for this team.
        return await self.session.scalar(
            select(Team).where(Team.id == team_id, Team.workspace_id == workspace).with_for_update()
        )

    async def member(self, team_id: UUID, user_id: UUID):
        return await self.session.scalar(
            select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )

    async def add(self, member: TeamMember):
        self.session.add(member)
        await self.session.flush()

    async def delete(self, member: TeamMember):
        await self.session.delete(member)
