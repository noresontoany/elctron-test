import asyncio
from contextlib import asynccontextmanager
from time import perf_counter
from urllib.parse import urlsplit

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
from src.ship.metrics import HTTP_SECONDS


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


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    if request.url.path != "/internal/metrics":
        HTTP_SECONDS.labels(
            request.method, getattr(route, "path", "unmatched"), str(response.status_code)
        ).observe(perf_counter() - started)
    return response


@app.get("/internal/metrics", include_in_schema=False)
async def metrics():
    # Internal Docker network only. Caddy forwards /api/*, never /internal/*.
    return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})


@app.middleware("http")
async def same_origin_writes(request: Request, call_next):
    if request.method in {"POST", "PATCH", "DELETE", "PUT"}:
        origin = request.headers.get("origin")
        configured = urlsplit(get_settings().app_origin)
        allowed = {get_settings().app_origin}
        if configured.hostname in {"localhost", "127.0.0.1"}:
            # Keep both loopback names available, but no loopback alias for a VPS domain.
            port = f":{configured.port}" if configured.port else ""
            allowed.update(
                f"{configured.scheme}://{host}{port}" for host in ("localhost", "127.0.0.1")
            )
        allowed.update(
            filter(None, (item.strip() for item in get_settings().app_extra_origins.split(",")))
        )
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
