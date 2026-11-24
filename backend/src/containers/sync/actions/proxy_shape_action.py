import httpx
from fastapi import HTTPException, Request, Response

from src.containers.order.resources.order_resource import OrderResource
from src.containers.team.resources.directory_resource import (
    MemberResource,
    TeamResource,
    UserResource,
)
from src.ship.config import get_settings
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
        try:
            # Bounded long-polling, no SSE: one response at a time, cancellation closes upstream.
            upstream = await request.app.state.http.get(
                f"{settings.electric_url}/v1/shape",
                params=params,
            )
        except httpx.HTTPError:
            raise HTTPException(502, "Синхронизация временно недоступна") from None
        headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.startswith("electric-") or key == "content-type"
        }
        # Never share authenticated shape responses through a browser/shared HTTP cache.
        headers["cache-control"] = "private, no-store"
        headers["vary"] = "Cookie, Authorization"
        return Response(upstream.content, status_code=upstream.status_code, headers=headers)
