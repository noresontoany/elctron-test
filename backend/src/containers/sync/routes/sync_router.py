from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.containers.sync.actions.proxy_shape_action import ProxyShapeAction
from src.ship.auth import Actor, get_actor

router = APIRouter(prefix="/sync", tags=["Electric proxy"])


@router.get("/{resource}")
async def shape(resource: str, request: Request, actor: Annotated[Actor, Depends(get_actor)]):
    return await ProxyShapeAction().run(request, actor.workspace, resource)
