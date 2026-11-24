"""Integration tests against this demo's running Compose stack (no SKUD dependencies)."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

CREATED_IDS: list[str] = []

BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8097")


@pytest.fixture(scope="session", autouse=True)
def clean_up_test_records():
    yield
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[2] / "scripts/cleanup_test_orders.py"),
        ],
        input=json.dumps(CREATED_IDS),
        text=True,
        check=True,
    )


@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=25) as client:
        response = await client.post("/api/session", json={"workspace": "lab"})
        assert response.status_code == 200
        yield client


def body():
    return {
        "id": str(uuid4()),
        "title": "API Test repair",
        "bike": "Test Bike",
        "customer_name": "API Test",
        "estimate": 1500,
    }


async def create(client):
    response = await client.post("/api/orders", json=body())
    assert response.status_code == 201, response.text
    result = response.json()
    CREATED_IDS.append(result["order"]["id"])
    return result


async def test_session_and_origin_boundary():
    async with httpx.AsyncClient(base_url=BASE_URL) as anonymous:
        assert (await anonymous.get("/api/sync/orders", params={"offset": "-1"})).status_code == 401
        assert (await anonymous.post("/api/orders", json=body())).status_code == 401
        forged = await anonymous.post(
            "/api/session", json={}, headers={"Origin": "https://evil.test"}
        )
        assert forged.status_code == 403
        bad_workspace = await anonymous.post("/api/session", json={"workspace": "unknown"})
        assert bad_workspace.status_code == 422


async def test_crud_validation_conflict_and_resource(client):
    created = await create(client)
    order = created["order"]
    assert isinstance(created["txid"], int)
    assert "workspace_id" not in order
    order_id = order["id"]
    try:
        null = await client.patch(f"/api/orders/{order_id}", json={"version": 1, "title": None})
        assert null.status_code == 422
        invalid = await client.patch(
            f"/api/orders/{order_id}", json={"version": 1, "estimate": -10}
        )
        assert invalid.status_code == 422
        injection = await client.patch(
            f"/api/orders/{order_id}", json={"version": 1, "workspace_id": "studio"}
        )
        assert injection.status_code == 422
        results = await asyncio.gather(
            *[
                client.patch(
                    f"/api/orders/{order_id}", json={"version": 1, "title": f"API Test {i}"}
                )
                for i in range(2)
            ]
        )
        assert sorted(result.status_code for result in results) == [200, 409]
        updated = next(result.json() for result in results if result.status_code == 200)
        assert updated["order"]["version"] == 2
        deleted = await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 2})
        assert deleted.status_code == 200
        assert deleted.json()["order"] is None
    finally:
        await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 2})
        await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 1})


async def test_workspace_filter_cannot_be_overridden(client):
    created = await create(client)
    order_id = created["order"]["id"]
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=25) as studio:
            await studio.post("/api/session", json={"workspace": "studio"})
            denied = await studio.patch(
                f"/api/orders/{order_id}", json={"version": 1, "title": "stolen"}
            )
            assert denied.status_code == 404
            shape = await studio.get(
                "/api/sync/orders",
                params={
                    "offset": "-1",
                    "table": "demo_seeds",
                    "where": "1=1",
                    "params[1]": "lab",
                    "columns": "workspace_id",
                    "secret": "fake",
                },
            )
            assert shape.status_code == 200, shape.text
            records = [message["value"] for message in shape.json() if "value" in message]
            assert all(record["id"] != order_id for record in records)
            assert all("workspace_id" not in record for record in records)
            assert shape.headers["cache-control"] == "private, no-store"
    finally:
        await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 1})


async def test_txid_arrives_in_electric_stream(client):
    snapshot = await client.get("/api/sync/orders", params={"offset": "-1"})
    assert snapshot.status_code == 200
    created = await create(client)
    order_id = created["order"]["id"]
    try:
        changes = await client.get(
            "/api/sync/orders",
            params={
                "offset": snapshot.headers["electric-offset"],
                "handle": snapshot.headers["electric-handle"],
                "live": "true",
            },
        )
        assert changes.status_code == 200, changes.text
        records = [item for item in changes.json() if item.get("value", {}).get("id") == order_id]
        assert records
        assert created["txid"] in records[0]["headers"]["txids"]
    finally:
        await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 1})


async def test_custom_operation_and_status_rules(client):
    created = await create(client)
    order_id = created["order"]["id"]
    denied = await client.post(f"/api/orders/{order_id}/deliver", json={"version": 1})
    assert denied.status_code == 409
    bypass = await client.patch(
        f"/api/orders/{order_id}", json={"version": 1, "status": "delivered"}
    )
    assert bypass.status_code == 409
    jump = await client.patch(f"/api/orders/{order_id}", json={"version": 1, "status": "ready"})
    assert jump.status_code == 409
    for version, status in [(1, "repair"), (2, "ready")]:
        result = await client.patch(
            f"/api/orders/{order_id}", json={"version": version, "status": status}
        )
        assert result.status_code == 200
    deletion = await client.request("DELETE", f"/api/orders/{order_id}", json={"version": 3})
    assert deletion.status_code == 409
    delivered = await client.post(f"/api/orders/{order_id}/deliver", json={"version": 3})
    assert delivered.status_code == 200
    assert delivered.json()["order"]["status"] == "delivered"
    assert delivered.json()["order"]["version"] == 4
    repeated = await client.post(f"/api/orders/{order_id}/deliver", json={"version": 4})
    assert repeated.status_code == 409
    edited = await client.patch(f"/api/orders/{order_id}", json={"version": 4, "title": "reopen"})
    assert edited.status_code == 409


async def directory(client, resource):
    # offset=-1 returns a log (snapshot + changes), not a ready-made row array.
    rows = {}
    params = {"offset": "-1"}
    for _ in range(100):
        response = await client.get(f"/api/sync/{resource}", params=params)
        assert response.status_code == 200, response.text
        for message in response.json():
            headers = message.get("headers", {})
            value = message.get("value")
            if value:
                if headers.get("operation") == "delete":
                    rows.pop(value["id"], None)
                else:
                    rows[value["id"]] = {**rows.get(value["id"], {}), **value}
            if headers.get("control") == "up-to-date":
                return list(rows.values())
        params = {
            "offset": response.headers["electric-offset"],
            "handle": response.headers["electric-handle"],
        }
    raise AssertionError("Electric snapshot did not complete")


async def identity(client, user_id):
    response = await client.post("/api/session", json={"workspace": "lab", "user_id": user_id})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


async def test_claim_race_membership_and_server_permissions(client):
    manager = (await client.post("/api/session", json={"workspace": "lab"})).json()
    manager_header = {"Authorization": f"Bearer {manager['token']}"}
    client.headers.update(manager_header)
    users = {row["name"]: row for row in manager["users"]}
    alex = await identity(client, users["Алексей"]["id"])
    nikita = await identity(client, users["Никита"]["id"])
    maria = await identity(client, users["Мария"]["id"])
    order = (await create(client))["order"]
    url = f"/api/orders/{order['id']}"
    denied = await client.post(f"{url}/claim", headers=maria, json={"version": 1})
    assert denied.status_code == 409  # Not a member of this team.
    forbidden = await client.patch(url, headers=alex, json={"version": 1, "title": "stolen"})
    assert forbidden.status_code == 403
    race = await asyncio.gather(
        *[
            client.post(f"{url}/claim", headers=actor, json={"version": 1})
            for actor in (alex, nikita)
        ]
    )
    assert sorted(result.status_code for result in race) == [200, 409]
    winner_index = next(i for i, result in enumerate(race) if result.status_code == 200)
    won = race[winner_index].json()["order"]
    assert won["version"] == 2 and won["status"] == "repair"
    winner_header = (alex, nikita)[winner_index]
    member = next(
        row
        for row in await directory(client, "team_members")
        if row["team_id"] == won["team_id"] and row["user_id"] == won["assignee_id"]
    )
    path = f"/api/teams/{won['team_id']}/members"
    removed = await client.delete(f"{path}/{won['assignee_id']}/{member['id']}")
    assert removed.status_code == 200
    try:
        denied = await client.post(f"{url}/deliver", headers=winner_header, json={"version": 2})
        assert denied.status_code == 403
        renamed = await client.patch(
            f"/api/users/{won['assignee_id']}",
            headers=winner_header,
            json={"version": 1, "name": "hacked"},
        )
        assert renamed.status_code == 403
    finally:
        restored = await client.post(
            path, json={"user_id": won["assignee_id"], "role": member["role"]}
        )
        assert restored.status_code == 201
    # Old delete requests cannot delete a newly added membership (ABA protection).
    stale = await client.delete(f"{path}/{won['assignee_id']}/{member['id']}")
    assert stale.status_code == 409
    # Token still identifies the winner even though the cookie belongs to Maria.
    updated = await client.patch(url, headers=winner_header, json={"version": 2, "status": "ready"})
    assert updated.status_code == 200
    assert updated.json()["order"]["assignee_id"] == won["assignee_id"]


async def test_related_shapes_tenant_boundary_and_rename_version(client):
    lab_users = await directory(client, "users")
    user = next(row for row in lab_users if row["name"] == "Мария")
    version = int(user["version"])
    response = await client.patch(
        f"/api/users/{user['id']}", json={"name": "Мария API", "version": version}
    )
    assert response.status_code == 200
    try:
        stale = await client.patch(
            f"/api/users/{user['id']}", json={"name": "stale", "version": version}
        )
        assert stale.status_code == 409
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=25) as studio:
            await studio.post("/api/session", json={"workspace": "studio"})
            for resource in ("users", "teams", "team_members"):
                own_ids = {row["id"] for row in await directory(client, resource)}
                response = await studio.get(
                    f"/api/sync/{resource}",
                    params={"offset": "-1", "where": "1=1", "params[1]": "lab"},
                )
                assert response.status_code == 200
                rows = [m["value"] for m in response.json() if "value" in m]
                assert all(row["id"] not in own_ids and "workspace_id" not in row for row in rows)
            assert (
                await studio.get("/api/sync/demo_seeds", params={"offset": "-1"})
            ).status_code == 404
            studio_user = (await directory(studio, "users"))[0]
            invalid = await client.post(
                "/api/orders", json={**body(), "assignee_id": studio_user["id"]}
            )
            assert invalid.status_code == 409
    finally:
        restored = await client.patch(
            f"/api/users/{user['id']}", json={"name": user["name"], "version": version + 1}
        )
        assert restored.status_code == 200
