import asyncio
from time import perf_counter

import httpx
from fastapi import HTTPException, Request, Response

from src.containers.order.resources.order_resource import OrderResource
from src.containers.team.resources.directory_resource import (
    MemberResource,
    TeamResource,
    UserResource,
)
from src.ship.config import get_settings
from src.ship.metrics import (
    SYNC_ACTIVE,
    SYNC_CANCELLED,
    SYNC_REJECTED,
    SYNC_UPSTREAM,
    SYNC_WAIT,
    SYNC_WAITING,
)
from src.ship.workspace import Workspace


class ProxyShapeAction:
    # Eager sync only; table, columns, where and credentials are always server-owned.
    protocol_params = {"offset", "handle", "live", "cursor", "replica", "log"}

    async def run(self, request: Request, workspace: Workspace, resource: str) -> Response:
        resources = {
            "orders": OrderResource,
            "users": UserResource,
            "teams": TeamResource,
            "team_members": MemberResource,
        }
        if resource not in resources:
            raise HTTPException(404, "Коллекция не найдена")
        settings = get_settings()
        params = {
            key: value for key, value in request.query_params.items() if key in self.protocol_params
        }
        params.update(
            {
                "table": resource,
                "where": "workspace_id = $1",
                "params[1]": workspace.value,
                "columns": ",".join(resources[resource].model_fields),
                "secret": settings.electric_secret,
            }
        )
        slots = request.app.state.sync_slots
        started = perf_counter()
        SYNC_WAITING.inc()
        try:
            await asyncio.wait_for(slots.acquire(), settings.sync_admission_timeout)
        except TimeoutError:
            SYNC_REJECTED.inc()
            raise HTTPException(
                503, "Лимит синхронизации достигнут", headers={"Retry-After": "1"}
            ) from None
        finally:
            SYNC_WAITING.dec()
            SYNC_WAIT.observe(perf_counter() - started)

        async def disconnected():
            while not await request.is_disconnected():
                await asyncio.sleep(0.2)

        SYNC_ACTIVE.inc()
        started = perf_counter()
        status = "cancelled"
        upstream_task = asyncio.create_task(
            request.app.state.http.get(
                f"{settings.electric_url}/v1/shape",
                params=params,
            )
        )
        disconnect_task = asyncio.create_task(disconnected())
        try:
            done, _ = await asyncio.wait(
                {upstream_task, disconnect_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if upstream_task not in done:
                return Response(status_code=499)
            upstream = upstream_task.result()
            status = str(upstream.status_code)
        except httpx.HTTPError:
            status = "502"
            raise HTTPException(502, "Синхронизация временно недоступна") from None
        finally:
            for task in (upstream_task, disconnect_task):
                if not task.done():
                    task.cancel()
            try:
                await asyncio.gather(upstream_task, disconnect_task, return_exceptions=True)
            finally:
                # An ASGI cancellation scope can cancel the cleanup await itself.
                if status == "cancelled":
                    SYNC_CANCELLED.inc()
                SYNC_UPSTREAM.labels(resource, status).observe(perf_counter() - started)
                SYNC_ACTIVE.dec()
                slots.release()
        headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.startswith("electric-") or key == "content-type"
        }
        # Never share authenticated shape responses through a browser/shared HTTP cache.
        headers["cache-control"] = "private, no-store"
        headers["vary"] = "Cookie, Authorization"
        return Response(upstream.content, status_code=upstream.status_code, headers=headers)
