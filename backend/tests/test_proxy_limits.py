"""Proxy admission/cancellation without a running database or changing server limits."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from src.containers.sync.actions import proxy_shape_action as proxy
from src.ship.workspace import Workspace


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setattr(
        proxy,
        "get_settings",
        lambda: SimpleNamespace(
            sync_admission_timeout=0.01,
            electric_url="http://electric.test",
            electric_secret="test-only",
        ),
    )


def request(client, slots, disconnected):
    return SimpleNamespace(
        query_params={"offset": "-1"},
        app=SimpleNamespace(state=SimpleNamespace(http=client, sync_slots=slots)),
        is_disconnected=disconnected,
    )


async def test_admission_rejects_instead_of_waiting_in_httpx_pool(settings):
    async def disconnected():
        return False

    async def unexpected(_):
        raise AssertionError("No upstream request should start without a slot")

    async with httpx.AsyncClient(transport=httpx.MockTransport(unexpected)) as client:
        with pytest.raises(HTTPException) as result:
            await proxy.ProxyShapeAction().run(
                request(client, asyncio.Semaphore(0), disconnected),
                Workspace("lab"),
                "orders",
            )
    assert result.value.status_code == 503
    assert result.value.headers == {"Retry-After": "1"}


async def test_disconnect_cancels_upstream_and_returns_slot(settings):
    started, cancelled, gone = asyncio.Event(), asyncio.Event(), asyncio.Event()
    slots = asyncio.Semaphore(1)

    async def upstream(_):
        started.set()
        try:
            await asyncio.sleep(60)
        finally:
            cancelled.set()
        return httpx.Response(200, json=[])

    async def disconnected():
        return gone.is_set()

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        task = asyncio.create_task(
            proxy.ProxyShapeAction().run(
                request(client, slots, disconnected),
                Workspace("lab"),
                "orders",
            )
        )
        await asyncio.wait_for(started.wait(), 1)
        assert slots.locked()
        gone.set()
        response = await asyncio.wait_for(task, 1)
        assert response.status_code == 499
        assert cancelled.is_set()
        assert not slots.locked()


async def test_upstream_failure_also_returns_slot(settings):
    slots = asyncio.Semaphore(1)

    async def upstream(_):
        raise httpx.ConnectError("offline")

    async def disconnected():
        return False

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        with pytest.raises(HTTPException) as result:
            await proxy.ProxyShapeAction().run(
                request(client, slots, disconnected), Workspace("lab"), "orders"
            )
        assert result.value.status_code == 502
        assert not slots.locked()
