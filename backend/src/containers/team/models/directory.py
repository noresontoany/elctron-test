from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.ship.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_users_workspace"),
        CheckConstraint("role IN ('manager','mechanic')", name="user_role"),
        CheckConstraint("version >= 1", name="user_version"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(60))
    role: Mapped[str] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(default=1)


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("id", "workspace_id", name="uq_teams_workspace"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(60))


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
        ForeignKeyConstraint(
            ["team_id", "workspace_id"], ["teams.id", "teams.workspace_id"], name="fk_member_team"
        ),
        ForeignKeyConstraint(
            ["user_id", "workspace_id"], ["users.id", "users.workspace_id"], name="fk_member_user"
        ),
        CheckConstraint("role IN ('lead','mechanic')", name="member_role"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[str] = mapped_column(String(32), index=True)
    team_id: Mapped[UUID] = mapped_column()
    user_id: Mapped[UUID] = mapped_column()
    role: Mapped[str] = mapped_column(String(16))
