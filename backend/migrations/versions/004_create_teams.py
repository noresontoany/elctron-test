"""Create teams."""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"


def upgrade():
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.UniqueConstraint("id", "workspace_id", name="uq_teams_workspace"),
    )
    op.create_index("ix_teams_workspace_id", "teams", ["workspace_id"])
    op.execute("ALTER TABLE teams REPLICA IDENTITY FULL")


def downgrade():
    op.drop_table("teams")
