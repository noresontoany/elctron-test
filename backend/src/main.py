import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.containers.order.routes.order_router import router as order_router
from src.containers.session.routes.session_router import router as session_router
from src.containers.sync.routes.sync_router import router as sync_router
from src.containers.team.routes.team_router import router as team_router
from src.ship.config import get_settings
from src.ship.database import engine
from src.ship.http_middleware import WorkshopHttpMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.sync_slots = asyncio.Semaphore(settings.sync_max_connections)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(65, connect=5, pool=1),
        limits=httpx.Limits(
            max_connections=settings.sync_max_connections,
            max_keepalive_connections=settings.sync_max_connections,
        ),
    ) as client:
        app.state.http = client
        yield
    await engine.dispose()


app = FastAPI(
    title="Spoke Workshop API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


app.add_middleware(WorkshopHttpMiddleware)


@app.get("/internal/metrics", include_in_schema=False)
async def metrics():
    # Internal Docker network only. Caddy forwards /api/*, never /internal/*.
    return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        {"detail": "Заказ с таким ID уже существует или данные нарушают ограничения"},
        status_code=409,
    )


@app.get("/api/health", tags=["Health"])
async def health():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(session_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(team_router, prefix="/api")
app.include_router(sync_router, prefix="/api")
