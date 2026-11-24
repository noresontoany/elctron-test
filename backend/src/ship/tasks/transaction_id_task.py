from src.ship.repositories.transaction_repository import TransactionRepository


class TransactionIdTask:
    async def run(self, repository: TransactionRepository) -> int:
        return await repository.flush_with_txid()
