"""Create the orders table. Demo data lives in the separate idempotent seeder."""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.String(32), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("bike", sa.String(100), nullable=False),
        sa.Column("customer_name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assignee", sa.String(60), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("estimate", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('queued','repair','ready','delivered')", name="order_status"
        ),
        sa.CheckConstraint("priority IN ('normal','urgent')", name="order_priority"),
        sa.CheckConstraint("estimate >= 0 AND estimate <= 1000000", name="order_estimate"),
        sa.CheckConstraint("version >= 1", name="order_version"),
        sa.CheckConstraint("workspace_id IN ('studio','lab')", name="order_workspace"),
    )
    op.create_index("ix_orders_workspace_id", "orders", ["workspace_id"])
    op.execute("ALTER TABLE orders REPLICA IDENTITY FULL")


def downgrade():
    op.drop_table("orders")
