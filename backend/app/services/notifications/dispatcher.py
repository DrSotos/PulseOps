"""Notification dispatcher that handles channel lookups, executions, and delivery tracking."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.endpoint import MonitoredEndpoint
from app.models.incident import Incident
from app.models.notification import NotificationChannel, NotificationDelivery
from app.services.notifications.email_sender import (
    build_incident_email,
    send_email_notification,
)
from app.services.notifications.webhook_sender import (
    build_incident_webhook_payload,
    send_webhook_notification,
)

logger = get_logger(__name__)


async def dispatch_incident_notifications(
    session: AsyncSession,
    incident: Incident,
    endpoint: MonitoredEndpoint,
    event_type: str = "incident_created",
) -> list[NotificationDelivery]:
    """Find user notification channels and execute dispatches."""
    stmt = select(NotificationChannel).where(
        NotificationChannel.user_id == endpoint.user_id,
        NotificationChannel.is_enabled == True,
    )
    result = await session.execute(stmt)
    channels = result.scalars().all()

    deliveries: list[NotificationDelivery] = []

    for channel in channels:
        delivery = NotificationDelivery(
            id=uuid.uuid4(),
            incident_id=incident.id,
            channel_id=channel.id,
            event_type=event_type,
            delivery_status="pending",
            attempts=0,
        )

        try:
            if channel.channel_type == "email":
                subject, html = build_incident_email(
                    endpoint_name=endpoint.name,
                    endpoint_url=endpoint.url,
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    description=incident.description,
                    detected_at=incident.started_at,
                    incident_id=str(incident.id),
                )
                success, err = await send_email_notification(
                    to_email=channel.destination,
                    subject=subject,
                    html_body=html,
                )
                delivery.attempts = 1
                delivery.last_attempt_at = datetime.now(UTC)
                delivery.delivery_status = "delivered" if success else "failed"
                delivery.error_message = err

            elif channel.channel_type == "webhook":
                payload = build_incident_webhook_payload(
                    endpoint_name=endpoint.name,
                    endpoint_url=endpoint.url,
                    endpoint_id=str(endpoint.id),
                    incident_id=str(incident.id),
                    incident_type=incident.incident_type,
                    severity=incident.severity,
                    status=incident.status,
                    description=incident.description,
                    event_type=event_type,
                )
                success, code, err = await send_webhook_notification(
                    url=channel.destination,
                    payload=payload,
                )
                delivery.attempts = 1
                delivery.last_attempt_at = datetime.now(UTC)
                delivery.response_status = code
                delivery.delivery_status = "delivered" if success else "failed"
                delivery.error_message = err

            else:
                delivery.delivery_status = "failed"
                delivery.error_message = f"Unsupported channel type: {channel.channel_type}"

        except Exception as e:  # noqa: BLE001
            delivery.delivery_status = "failed"
            delivery.attempts = 1
            delivery.last_attempt_at = datetime.now(UTC)
            delivery.error_message = f"Dispatch error: {str(e)[:300]}"
            logger.error(f"Error dispatching notification for channel {channel.id}: {e}")

        session.add(delivery)
        deliveries.append(delivery)

    if deliveries:
        await session.flush()

    return deliveries
