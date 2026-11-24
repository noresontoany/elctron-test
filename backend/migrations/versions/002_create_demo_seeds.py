"""Create the demo seed marker, separate from order schema and seed data."""

from alembic import op

revision = "002"
down_revision = "001"


def upgrade():
    op.execute("CREATE TABLE IF NOT EXISTS demo_seeds (name text PRIMARY KEY)")


def downgrade():
    op.drop_table("demo_seeds")
