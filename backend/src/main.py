from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.containers.order.routes.order_router import router as order_router
from src.containers.session.routes.session_router import router as session_router
from src.containers.sync.routes.sync_router import router as sync_router
from src.containers.team.routes.team_router import router as team_router
from src.ship.config import get_settings
from src.ship.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=65, limits=httpx.Limits(max_connections=100)) as client:
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


@app.middleware("http")
async def same_origin_writes(request: Request, call_next):
    if request.method in {"POST", "PATCH", "DELETE", "PUT"}:
        origin = request.headers.get("origin")
        configured = urlsplit(get_settings().app_origin)
        allowed = {
            get_settings().app_origin,
            f"{configured.scheme}://127.0.0.1:{configured.port or 80}",
        }
        if origin is not None and origin not in allowed:
            return JSONResponse({"detail": "Недопустимый Origin"}, status_code=403)
    return await call_next(request)


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
