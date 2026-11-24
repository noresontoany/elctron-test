"""Pure ASGI middleware: preserve http.disconnect for long-poll cancellation."""

import asyncio
from time import perf_counter
from urllib.parse import urlsplit

from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.ship.config import get_settings
from src.ship.metrics import HTTP_SECONDS


class WorkshopHttpMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = perf_counter()
        status = 500

        async def measured_send(message: Message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            if scope["method"] in {"POST", "PATCH", "DELETE", "PUT"}:
                origin = Headers(scope=scope).get("origin")
                settings = get_settings()
                configured = urlsplit(settings.app_origin)
                allowed = {settings.app_origin}
                if configured.hostname in {"localhost", "127.0.0.1"}:
                    port = f":{configured.port}" if configured.port else ""
                    allowed.update(
                        f"{configured.scheme}://{host}{port}" for host in ("localhost", "127.0.0.1")
                    )
                allowed.update(
                    filter(None, (item.strip() for item in settings.app_extra_origins.split(",")))
                )
                if origin is not None and origin not in allowed:
                    response = JSONResponse({"detail": "Недопустимый Origin"}, status_code=403)
                    return await response(scope, receive, measured_send)
            await self.app(scope, receive, measured_send)
        except asyncio.CancelledError:
            status = 499
            raise
        finally:
            if scope["path"] != "/internal/metrics":
                route = scope.get("route")
                HTTP_SECONDS.labels(
                    scope["method"], getattr(route, "path", "unmatched"), str(status)
                ).observe(perf_counter() - started)
