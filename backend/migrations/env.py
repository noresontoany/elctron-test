import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.containers.order.models.order import Order  # noqa: F401
from src.containers.team.models.directory import Team, TeamMember, User  # noqa: F401
from src.ship.base import Base
from src.ship.config import get_settings
from src.ship.seed_record import SeedRecord  # noqa: F401


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def main():
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


asyncio.run(main())
