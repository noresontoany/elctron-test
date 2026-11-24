"""Create team_members."""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"


def upgrade():
    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.String(32), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_member"),
        sa.ForeignKeyConstraint(
            ["team_id", "workspace_id"], ["teams.id", "teams.workspace_id"], name="fk_member_team"
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "workspace_id"], ["users.id", "users.workspace_id"], name="fk_member_user"
        ),
        sa.CheckConstraint("role IN ('lead','mechanic')", name="member_role"),
    )
    op.create_index("ix_team_members_workspace_id", "team_members", ["workspace_id"])
    op.execute("ALTER TABLE team_members REPLICA IDENTITY FULL")


def downgrade():
    op.drop_table("team_members")
