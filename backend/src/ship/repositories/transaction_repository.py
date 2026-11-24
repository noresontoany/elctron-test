from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def flush_with_txid(self) -> int:
        await self.session.flush()
        # Electric exposes the 32-bit xid, not the epoch-extended xid8.
        return int(
            await self.session.scalar(
                text("SELECT pg_current_xact_id()::text::bigint % 4294967296")
            )
        )
