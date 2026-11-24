"""Create users."""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("id", "workspace_id", name="uq_users_workspace"),
        sa.CheckConstraint("role IN ('manager','mechanic')", name="user_role"),
        sa.CheckConstraint("version >= 1", name="user_version"),
    )
    op.create_index("ix_users_workspace_id", "users", ["workspace_id"])
    op.execute("ALTER TABLE users REPLICA IDENTITY FULL")


def downgrade():
    op.drop_table("users")
