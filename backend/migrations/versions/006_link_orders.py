"""Backfill relations without changing existing order status, price or version."""

from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"


def key(workspace, kind, slug):
    return uuid5(NAMESPACE_URL, f"spoke/{workspace}/{kind}/{slug}")


def upgrade():
    db = op.get_bind()
    op.add_column("orders", sa.Column("team_id", sa.Uuid(), nullable=True))
    op.add_column("orders", sa.Column("assignee_id", sa.Uuid(), nullable=True))
    for ws in ("studio", "lab"):
        names = {"Ирина", "Алексей", "Мария", "Никита"}
        names.update(
            db.execute(
                sa.text(
                    "SELECT DISTINCT assignee FROM orders "
                    "WHERE workspace_id=:ws AND assignee != 'Не назначен'"
                ),
                {"ws": ws},
            ).scalars()
        )
        for name in sorted(names):
            db.execute(
                sa.text(
                    "INSERT INTO users (id,workspace_id,name,role,version) "
                    "VALUES (:id,:ws,:name,:role,1)"
                ),
                {
                    "id": key(ws, "user", name),
                    "ws": ws,
                    "name": name,
                    "role": "manager" if name == "Ирина" else "mechanic",
                },
            )
        for slug, name in (("service", "Сервис и ТО"), ("wheels", "Колёса и сборка")):
            team_id = key(ws, "team", slug)
            db.execute(
                sa.text("INSERT INTO teams (id,workspace_id,name) VALUES (:id,:ws,:name)"),
                {"id": team_id, "ws": ws, "name": name},
            )
            members = names - {"Мария"} if slug == "service" else {"Ирина", "Мария"}
            for name in sorted(members):
                db.execute(
                    sa.text(
                        "INSERT INTO team_members (id,workspace_id,team_id,user_id,role) "
                        "VALUES (:id,:ws,:team,:user,:role)"
                    ),
                    {
                        "id": key(ws, "member", f"{slug}/{name}"),
                        "ws": ws,
                        "team": team_id,
                        "user": key(ws, "user", name),
                        "role": "lead" if name == "Ирина" else "mechanic",
                    },
                )
        db.execute(
            sa.text("UPDATE orders SET team_id=:service WHERE workspace_id=:ws"),
            {"ws": ws, "service": key(ws, "team", "service")},
        )
        db.execute(
            sa.text(
                "UPDATE orders SET team_id=:wheels WHERE workspace_id=:ws AND assignee='Мария'"
            ),
            {"ws": ws, "wheels": key(ws, "team", "wheels")},
        )
        for name in names:
            db.execute(
                sa.text(
                    "UPDATE orders SET assignee_id=:user WHERE workspace_id=:ws AND assignee=:name"
                ),
                {"ws": ws, "user": key(ws, "user", name), "name": name},
            )
    op.alter_column("orders", "team_id", nullable=False)
    op.create_foreign_key(
        "fk_order_team", "orders", "teams", ["team_id", "workspace_id"], ["id", "workspace_id"]
    )
    op.create_foreign_key(
        "fk_order_assignee",
        "orders",
        "users",
        ["assignee_id", "workspace_id"],
        ["id", "workspace_id"],
    )
    op.create_index("ix_orders_team_id", "orders", ["team_id"])
    op.create_index("ix_orders_assignee_id", "orders", ["assignee_id"])
    op.drop_column("orders", "assignee")


def downgrade():
    op.add_column(
        "orders", sa.Column("assignee", sa.String(60), nullable=False, server_default="Не назначен")
    )
    op.execute("UPDATE orders SET assignee=users.name FROM users WHERE orders.assignee_id=users.id")
    op.alter_column("orders", "assignee", server_default=None)
    op.drop_index("ix_orders_assignee_id", "orders")
    op.drop_index("ix_orders_team_id", "orders")
    op.drop_constraint("fk_order_assignee", "orders", type_="foreignkey")
    op.drop_constraint("fk_order_team", "orders", type_="foreignkey")
    op.drop_column("orders", "assignee_id")
    op.drop_column("orders", "team_id")
