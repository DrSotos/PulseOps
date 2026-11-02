"""Incidents and event timeline REST API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import PaginationParams, get_current_user
from app.api.v1.schemas.incidents import (
    IncidentEventResponse,
    IncidentListResponse,
    IncidentResponse,
)
from app.api.v1.schemas.notifications import NotificationDeliveryResponse
from app.db.session import get_db
from app.models.endpoint import MonitoredEndpoint
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.notification import NotificationDelivery
from app.models.user import User

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    severity: Annotated[str | None, Query()] = None,
    endpoint_id: Annotated[uuid.UUID | None, Query()] = None,
):
    """List incidents filtered by status, severity, or endpoint."""
    conditions = [MonitoredEndpoint.user_id == current_user.id]

    if status_filter:
        conditions.append(Incident.status == status_filter)
    if severity:
        conditions.append(Incident.severity == severity)
    if endpoint_id:
        conditions.append(Incident.endpoint_id == endpoint_id)

    # Count
    count_stmt = (
        select(func.count(Incident.id))
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(and_(*conditions))
    )
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Query with join to retrieve endpoint metadata
    stmt = (
        select(Incident, MonitoredEndpoint.name, MonitoredEndpoint.url)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(and_(*conditions))
        .order_by(desc(Incident.started_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    res = await session.execute(stmt)
    rows = res.all()

    items: list[IncidentResponse] = []
    now = datetime.now(UTC)
    for inc, ep_name, ep_url in rows:
        resp = IncidentResponse.model_validate(inc)
        resp.endpoint_name = ep_name
        resp.endpoint_url = ep_url
        end_time = inc.resolved_at or now
        resp.duration_seconds = int((end_time - inc.started_at).total_seconds())
        items.append(resp)

    return IncidentListResponse(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve full incident details including chronological timeline events."""
    stmt = (
        select(Incident, MonitoredEndpoint.name, MonitoredEndpoint.url)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(
            and_(
                Incident.id == incident_id,
                MonitoredEndpoint.user_id == current_user.id,
            )
        )
        .options(selectinload(Incident.events))
    )
    res = await session.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    inc, ep_name, ep_url = row
    resp = IncidentResponse.model_validate(inc)
    resp.endpoint_name = ep_name
    resp.endpoint_url = ep_url
    end_time = inc.resolved_at or datetime.now(UTC)
    resp.duration_seconds = int((end_time - inc.started_at).total_seconds())
    resp.events = [IncidentEventResponse.model_validate(e) for e in (inc.events or [])]
    return resp


@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
async def acknowledge_incident(
    incident_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark an ongoing incident as acknowledged."""
    stmt = (
        select(Incident)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(
            and_(
                Incident.id == incident_id,
                MonitoredEndpoint.user_id == current_user.id,
            )
        )
    )
    res = await session.execute(stmt)
    incident = res.scalars().first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if incident.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot acknowledge an already resolved incident.",
        )

    now = datetime.now(UTC)
    incident.status = "acknowledged"
    incident.acknowledged_at = now

    event = IncidentEvent(
        id=uuid.uuid4(),
        incident_id=incident.id,
        event_type="acknowledged",
        description=f"Incident acknowledged by user {current_user.email}",
        metadata_json={"acknowledged_by": str(current_user.id)},
    )
    session.add(event)
    await session.commit()
    await session.refresh(incident)

    return IncidentResponse.model_validate(incident)


@router.get("/{incident_id}/events", response_model=list[IncidentEventResponse])
async def list_incident_events(
    incident_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve event timeline history for an incident."""
    # Verify ownership
    check_stmt = (
        select(Incident.id)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(
            and_(
                Incident.id == incident_id,
                MonitoredEndpoint.user_id == current_user.id,
            )
        )
    )
    res = await session.execute(check_stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    events_stmt = (
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at.asc())
    )
    e_res = await session.execute(events_stmt)
    events = e_res.scalars().all()
    return [IncidentEventResponse.model_validate(e) for e in events]


@router.get("/{incident_id}/notifications", response_model=list[NotificationDeliveryResponse])
async def list_incident_notifications(
    incident_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve delivery logs for notifications sent for this incident."""
    check_stmt = (
        select(Incident.id)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(
            and_(
                Incident.id == incident_id,
                MonitoredEndpoint.user_id == current_user.id,
            )
        )
    )
    res = await session.execute(check_stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    deliv_stmt = (
        select(NotificationDelivery)
        .where(NotificationDelivery.incident_id == incident_id)
        .order_by(desc(NotificationDelivery.created_at))
    )
    d_res = await session.execute(deliv_stmt)
    deliveries = d_res.scalars().all()
    return [NotificationDeliveryResponse.model_validate(d) for d in deliveries]
