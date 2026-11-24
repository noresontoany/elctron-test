from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.containers.order.actions.claim_order_action import ClaimOrderAction
from src.containers.order.actions.create_order_action import CreateOrderAction
from src.containers.order.actions.delete_order_action import DeleteOrderAction
from src.containers.order.actions.deliver_order_action import DeliverOrderAction
from src.containers.order.actions.update_order_action import UpdateOrderAction
from src.containers.order.requests.create_order_request import CreateOrderRequest
from src.containers.order.requests.update_order_request import UpdateOrderRequest
from src.containers.order.requests.version_request import VersionRequest
from src.containers.order.resources.mutation_resource import MutationResource
from src.ship.auth import Actor, get_actor
from src.ship.database import get_session

router = APIRouter(prefix="/orders", tags=["Orders"])
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentActor = Annotated[Actor, Depends(get_actor)]


@router.post("", response_model=MutationResource, status_code=201)
async def create_order(body: CreateOrderRequest, session: Session, actor: CurrentActor):
    return await CreateOrderAction().run(session, body, actor)


@router.patch("/{order_id}", response_model=MutationResource)
async def update_order(
    order_id: UUID, body: UpdateOrderRequest, session: Session, actor: CurrentActor
):
    return await UpdateOrderAction().run(session, body, actor, order_id)


@router.delete("/{order_id}", response_model=MutationResource)
async def delete_order(order_id: UUID, body: VersionRequest, session: Session, actor: CurrentActor):
    return await DeleteOrderAction().run(session, body, actor, order_id)


@router.post("/{order_id}/deliver", response_model=MutationResource)
async def deliver_order(
    order_id: UUID, body: VersionRequest, session: Session, actor: CurrentActor
):
    return await DeliverOrderAction().run(session, body, actor, order_id)


@router.post("/{order_id}/claim", response_model=MutationResource)
async def claim_order(order_id: UUID, body: VersionRequest, session: Session, actor: CurrentActor):
    return await ClaimOrderAction().run(session, body, actor, order_id)
