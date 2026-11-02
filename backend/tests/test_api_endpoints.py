"""Integration tests for Monitored Endpoints API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_endpoint_crud(client: AsyncClient, auth_headers: dict):
    # 1. Create Endpoint
    payload = {
        "name": "Production Auth API",
        "url": "https://httpbin.org/status/200",
        "http_method": "GET",
        "monitoring_interval": 60,
        "timeout": 10,
        "expected_status_codes": [200],
        "performance_threshold_ms": 1500,
    }
    create_resp = await client.post(
        "/api/v1/endpoints", json=payload, headers=auth_headers
    )
    assert create_resp.status_code == 201
    ep = create_resp.json()
    ep_id = ep["id"]
    assert ep["name"] == "Production Auth API"
    assert ep["is_active"] is True

    # 2. List Endpoints
    list_resp = await client.get("/api/v1/endpoints", headers=auth_headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == ep_id for item in list_data["items"])

    # 3. Get Endpoint Detail
    get_resp = await client.get(f"/api/v1/endpoints/{ep_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ep_id

    # 4. Update Endpoint
    patch_resp = await client.patch(
        f"/api/v1/endpoints/{ep_id}",
        json={"name": "Renamed Auth API", "monitoring_interval": 120},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Renamed Auth API"
    assert patch_resp.json()["monitoring_interval"] == 120

    # 5. Pause and Resume
    pause_resp = await client.post(
        f"/api/v1/endpoints/{ep_id}/pause", headers=auth_headers
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["is_active"] is False

    resume_resp = await client.post(
        f"/api/v1/endpoints/{ep_id}/resume", headers=auth_headers
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["is_active"] is True

    # 6. Delete Endpoint
    del_resp = await client.delete(
        f"/api/v1/endpoints/{ep_id}", headers=auth_headers
    )
    assert del_resp.status_code == 204

    # Verify not found after delete
    get_deleted = await client.get(f"/api/v1/endpoints/{ep_id}", headers=auth_headers)
    assert get_deleted.status_code == 404

