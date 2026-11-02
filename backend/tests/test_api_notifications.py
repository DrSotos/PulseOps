"""Integration tests for Notification Channels and Deliveries."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notification_channels_crud(client: AsyncClient, auth_headers: dict):
    # 1. Create Webhook Channel
    wh_payload = {
        "name": "DevOps Slack Bridge",
        "channel_type": "webhook",
        "destination": "https://httpbin.org/post",
        "is_enabled": True,
    }
    resp = await client.post(
        "/api/v1/notifications/channels", json=wh_payload, headers=auth_headers
    )
    assert resp.status_code == 201
    wh = resp.json()
    wh_id = wh["id"]
    assert wh["name"] == "DevOps Slack Bridge"

    # 2. List channels
    list_resp = await client.get("/api/v1/notifications/channels", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(c["id"] == wh_id for c in list_resp.json())

    # 3. Update channel
    up_resp = await client.patch(
        f"/api/v1/notifications/channels/{wh_id}",
        json={"name": "Updated Webhook Channel"},
        headers=auth_headers,
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["name"] == "Updated Webhook Channel"

    # 4. Test Webhook delivery
    test_resp = await client.post(
        f"/api/v1/notifications/channels/{wh_id}/test", headers=auth_headers
    )
    assert test_resp.status_code == 200
    assert test_resp.json()["success"] is True

    # 5. Delete channel
    del_resp = await client.delete(
        f"/api/v1/notifications/channels/{wh_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

