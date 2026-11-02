"""Incident detection, state machine, deduplication, and automated recovery engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.check import MonitoringCheck
from app.models.endpoint import MonitoredEndpoint
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.services.events import event_manager
from app.services.notifications.dispatcher import dispatch_incident_notifications

logger = get_logger(__name__)

# Incident Types
INCIDENT_OUTAGE = "outage"
INCIDENT_HIGH_LATENCY = "high_latency"
INCIDENT_UNEXPECTED_STATUS = "unexpected_status"
INCIDENT_RESPONSE_VALIDATION = "response_validation"
INCIDENT_SSL_ERROR = "ssl_error"

FAILURE_MAP = {
    "connection_error": INCIDENT_OUTAGE,
    "dns_error": INCIDENT_OUTAGE,
    "timeout": INCIDENT_OUTAGE,
    "ssl_error": INCIDENT_SSL_ERROR,
    "unexpected_status": INCIDENT_UNEXPECTED_STATUS,
    "content_mismatch": INCIDENT_RESPONSE_VALIDATION,
    "response_validation": INCIDENT_RESPONSE_VALIDATION,
    "performance_threshold": INCIDENT_HIGH_LATENCY,
}


def _severity_rank(sev: str) -> int:
    ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return ranks.get(sev.lower(), 1)


def determine_severity(incident_type: str, consecutive_failures: int) -> str:
    """Classify incident severity deterministically."""
    if incident_type == INCIDENT_OUTAGE:
        if consecutive_failures >= 10:
            return "critical"
        elif consecutive_failures >= 5:
            return "high"
        return "medium"
    elif incident_type == INCIDENT_HIGH_LATENCY:
        return "low"
    elif incident_type == INCIDENT_SSL_ERROR:
        return "high"
    return "medium"


async def get_recent_checks(
    session: AsyncSession, endpoint_id: uuid.UUID, limit: int = 25
) -> list[MonitoringCheck]:
    """Retrieve chronologically descending checks for an endpoint."""
    stmt = (
        select(MonitoringCheck)
        .where(MonitoringCheck.endpoint_id == endpoint_id)
        .order_by(desc(MonitoringCheck.created_at))
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def count_consecutive_failures(
    session: AsyncSession, endpoint_id: uuid.UUID
) -> int:
    checks = await get_recent_checks(session, endpoint_id, limit=30)
    count = 0
    for c in checks:
        if not c.is_successful:
            count += 1
        else:
            break
    return count


async def count_consecutive_successes(
    session: AsyncSession, endpoint_id: uuid.UUID
) -> int:
    checks = await get_recent_checks(session, endpoint_id, limit=20)
    count = 0
    for c in checks:
        if c.is_successful:
            count += 1
        else:
            break
    return count


async def get_active_incident(
    session: AsyncSession, endpoint_id: uuid.UUID, incident_type: str
) -> Incident | None:
    """Fetch active incident for deduplication."""
    stmt = select(Incident).where(
        and_(
            Incident.endpoint_id == endpoint_id,
            Incident.incident_type == incident_type,
            Incident.status.in_(["detected", "open", "acknowledged"]),
        )
    )
    res = await session.execute(stmt)
    return res.scalars().first()


async def create_incident(
    session: AsyncSession,
    endpoint: MonitoredEndpoint,
    incident_type: str,
    severity: str,
    description: str,
) -> Incident:
    """Create a new incident record with event log."""
    now = datetime.now(UTC)
    incident = Incident(
        id=uuid.uuid4(),
        endpoint_id=endpoint.id,
        incident_type=incident_type,
        severity=severity,
        status="open",
        description=description,
        started_at=now,
    )
    session.add(incident)

    event = IncidentEvent(
        id=uuid.uuid4(),
        incident_id=incident.id,
        event_type="detected",
        description=f"Incident opened: {description}",
        metadata_json={"consecutive_failures": settings.INCIDENT_FAILURE_THRESHOLD},
    )
    session.add(event)
    await session.flush()

    logger.warning(
        f"🚨 Incident #{incident.id} created for {endpoint.name} "
        f"[{severity.upper()}] {incident_type}: {description}"
    )

    # Real-time SSE dispatch to the endpoint's user
    await event_manager.publish_to_user(
        str(endpoint.user_id),
        "incident_created",
        {
            "incident_id": str(incident.id),
            "endpoint_id": str(endpoint.id),
            "endpoint_name": endpoint.name,
            "type": incident_type,
            "severity": severity,
            "status": "open",
            "description": description,
            "timestamp": now.isoformat(),
        },
    )

    # Trigger notifications
    await dispatch_incident_notifications(session, incident, endpoint, event_type="incident_created")
    return incident


async def resolve_incident(
    session: AsyncSession,
    incident: Incident,
    endpoint: MonitoredEndpoint,
) -> None:
    """Resolve an incident and emit recovery events."""
    now = datetime.now(UTC)
    incident.status = "resolved"
    incident.resolved_at = now

    event = IncidentEvent(
        id=uuid.uuid4(),
        incident_id=incident.id,
        event_type="resolved",
        description="Endpoint health recovered after consecutive successful checks. Auto-resolved.",
        metadata_json={"recovered_at": now.isoformat()},
    )
    session.add(event)
    await session.flush()

    logger.info(f"✅ Incident #{incident.id} resolved for {endpoint.name}")

    await event_manager.publish_to_user(
        str(endpoint.user_id),
        "incident_resolved",
        {
            "incident_id": str(incident.id),
            "endpoint_id": str(endpoint.id),
            "endpoint_name": endpoint.name,
            "status": "resolved",
            "resolved_at": now.isoformat(),
        },
    )

    await dispatch_incident_notifications(session, incident, endpoint, event_type="incident_resolved")


async def process_check_result(
    session: AsyncSession,
    endpoint: MonitoredEndpoint,
    check: MonitoringCheck,
) -> None:
    """Core evaluation loop executed after each monitoring check."""
    if check.failure_type == "internal_error":
        return

    # Broadcast check result via SSE
    await event_manager.publish_to_user(
        str(endpoint.user_id),
        "check_completed",
        {
            "endpoint_id": str(endpoint.id),
            "is_successful": check.is_successful,
            "response_time_ms": check.response_time_ms,
            "status_code": check.status_code,
            "failure_type": check.failure_type,
            "timestamp": check.completed_at.isoformat(),
        },
    )

    if not check.is_successful:
        incident_type = FAILURE_MAP.get(check.failure_type, INCIDENT_OUTAGE)
        failures = await count_consecutive_failures(session, endpoint.id)

        if failures >= settings.INCIDENT_FAILURE_THRESHOLD:
            existing = await get_active_incident(session, endpoint.id, incident_type)
            if existing is None:
                sev = determine_severity(incident_type, failures)
                desc = f"{endpoint.name} failed ({check.error_message or 'Service unavailable'})"
                await create_incident(session, endpoint, incident_type, sev, desc)
                await session.commit()
            else:
                # Deduplication: already open incident. Update severity or log periodic failures
                new_sev = determine_severity(incident_type, failures)
                if _severity_rank(new_sev) > _severity_rank(existing.severity):
                    existing.severity = new_sev
                    esc_event = IncidentEvent(
                        id=uuid.uuid4(),
                        incident_id=existing.id,
                        event_type="escalated",
                        description=f"Severity escalated to {new_sev} after {failures} consecutive failed probes.",
                    )
                    session.add(esc_event)
                    await session.commit()
    else:
        # Check succeeded: check if we should resolve active incidents
        successes = await count_consecutive_successes(session, endpoint.id)
        if successes >= settings.INCIDENT_RECOVERY_THRESHOLD:
            stmt = select(Incident).where(
                and_(
                    Incident.endpoint_id == endpoint.id,
                    Incident.status.in_(["detected", "open", "acknowledged"]),
                )
            )
            res = await session.execute(stmt)
            active = list(res.scalars().all())

            for inc in active:
                await resolve_incident(session, inc, endpoint)

            if active:
                await session.commit()
