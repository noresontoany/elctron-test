"""Remove only explicitly recorded test UUIDs from this project's database."""
import json
import subprocess
import sys
from pathlib import Path
from uuid import UUID

ids = [str(UUID(value)) for value in json.load(sys.stdin)]
if not ids:
    raise SystemExit(0)
code = '''import asyncio, json, sys
from uuid import UUID
from sqlalchemy import delete
from src.ship.database import session_factory, engine
from src.containers.order.models.order import Order
ids = [UUID(value) for value in json.load(sys.stdin)]
async def cleanup():
    async with session_factory() as session, session.begin():
        await session.execute(delete(Order).where(Order.id.in_(ids), Order.customer_name.in_(["API Test", "E2E Test"])))
    await engine.dispose()
asyncio.run(cleanup())
'''
subprocess.run(['docker', 'compose', 'exec', '-T', 'api', 'python', '-c', code],
               cwd=Path(__file__).resolve().parents[1], input=json.dumps(ids), text=True, check=True)
