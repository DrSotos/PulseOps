"""Webhook notification sender with JSON payload delivery."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_webhook_notification(
    url: str,
    payload: dict[str, Any],
    timeout: int | None = None,
) -> tuple[bool, int | None, str | None]:
    """Deliver a webhook payload to the user-configured destination.

    Returns:
        (success, response_http_status, error_message)
    """
    to_val = timeout or settings.WEBHOOK_TIMEOUT
    event_id = str(uuid.uuid4())
    payload["event_id"] = event_id
    payload["timestamp"] = datetime.now(UTC).isoformat()

    try:
        async with httpx.AsyncClient(timeout=to_val) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PulseOps-Webhook-Notifier/1.0",
                    "X-PulseOps-Event-Id": event_id,
                },
            )
            if resp.status_code < 300:
                logger.info(f"Webhook delivered successfully to {url} (status={resp.status_code})")
                return True, resp.status_code, None
            else:
                msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning(f"Webhook returned error status from {url}: {msg}")
                return False, resp.status_code, msg
    except httpx.TimeoutException:
        err = f"Webhook request timed out after {to_val} seconds."
        logger.error(f"Webhook to {url} timed out.")
        return False, None, err
    except Exception as e:  # noqa: BLE001
        err = f"Failed to deliver webhook ({type(e).__name__}): {str(e)[:300]}"
        logger.error(f"Webhook delivery failure to {url}: {err}")
        return False, None, err


def build_incident_webhook_payload(
    endpoint_name: str,
    endpoint_url: str,
    endpoint_id: str,
    incident_id: str,
    incident_type: str,
    severity: str,
    status: str,
    description: str,
    event_type: str = "incident_created",
) -> dict[str, Any]:
    """Structure JSON payload for automated webhook receivers."""
    return {
        "event_type": event_type,
        "incident": {
            "id": incident_id,
            "type": incident_type,
            "severity": severity,
            "status": status,
            "description": description,
        },
        "endpoint": {
            "id": endpoint_id,
            "name": endpoint_name,
            "url": endpoint_url,
        },
    }
