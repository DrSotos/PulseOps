"""Dashboard metrics, system health overview, and real-time activity feed."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.api.v1.schemas.dashboard import (
    ActivityItem,
    DashboardOverview,
    EndpointHealthSummary,
)
from app.db.session import get_db
from app.models.check import MonitoringCheck
from app.models.endpoint import MonitoredEndpoint
from app.models.incident import Incident
from app.models.incident_event import IncidentEvent
from app.models.user import User
from app.services.statistics.calculator import calculate_uptime, get_endpoint_status

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def get_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Compile high-level operational overview metrics for the main monitoring view."""
    # Fetch all endpoints for this user
    ep_stmt = select(MonitoredEndpoint).where(MonitoredEndpoint.user_id == current_user.id)
    ep_res = await session.execute(ep_stmt)
    endpoints = ep_res.scalars().all()

    total_endpoints = len(endpoints)
    operational = 0
    degraded = 0
    down = 0
    paused = 0

    endpoint_health_list: list[EndpointHealthSummary] = []
    total_uptimes: list[float] = []
    recent_latencies: list[float] = []

    for ep in endpoints:
        status_str = await get_endpoint_status(session, ep)
        if status_str == "operational":
            operational += 1
        elif status_str == "degraded":
            degraded += 1
        elif status_str == "down":
            down += 1
        elif status_str == "paused":
            paused += 1

        uptime_data = await calculate_uptime(session, ep.id, "24h")
        uptime_pct = uptime_data.get("uptime_percentage", 100.0)
        total_uptimes.append(uptime_pct)

        # Get latest check
        latest_c_stmt = (
            select(MonitoringCheck.response_time_ms)
            .where(
                and_(
                    MonitoringCheck.endpoint_id == ep.id,
                    MonitoringCheck.response_time_ms.isnot(None),
                )
            )
            .order_by(desc(MonitoringCheck.created_at))
            .limit(1)
        )
        latest_c_res = await session.execute(latest_c_stmt)
        latest_time = latest_c_res.scalar_one_or_none()
        if latest_time is not None:
            recent_latencies.append(latest_time)

        endpoint_health_list.append(
            EndpointHealthSummary(
                id=ep.id,
                name=ep.name,
                url=ep.url,
                http_method=ep.http_method,
                status=status_str,
                latest_response_time_ms=latest_time,
                uptime_percentage=uptime_pct,
                last_checked_at=ep.last_checked_at,
            )
        )

    # Active incidents count
    active_inc_stmt = (
        select(func.count(Incident.id))
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(
            and_(
                MonitoredEndpoint.user_id == current_user.id,
                Incident.status.in_(["detected", "open", "acknowledged"]),
            )
        )
    )
    inc_res = await session.execute(active_inc_stmt)
    active_incidents = inc_res.scalar_one()

    # Overall uptime
    overall_uptime = (
        round(sum(total_uptimes) / len(total_uptimes), 2) if total_uptimes else 100.0
    )
    avg_latency = (
        round(sum(recent_latencies) / len(recent_latencies), 2)
        if recent_latencies
        else None
    )

    # Recent activity items (incidents and check events)
    activity_items: list[ActivityItem] = []

    # Get recent incident events
    events_stmt = (
        select(IncidentEvent, Incident.severity, MonitoredEndpoint.name)
        .join(Incident, IncidentEvent.incident_id == Incident.id)
        .join(MonitoredEndpoint, Incident.endpoint_id == MonitoredEndpoint.id)
        .where(MonitoredEndpoint.user_id == current_user.id)
        .order_by(desc(IncidentEvent.created_at))
        .limit(10)
    )
    events_res = await session.execute(events_stmt)
    for evt, sev, ep_name in events_res.all():
        activity_items.append(
            ActivityItem(
                id=str(evt.id),
                type=f"incident_{evt.event_type}",
                title=f"{ep_name}: {evt.event_type.title()}",
                description=evt.description,
                timestamp=evt.created_at,
                severity=sev,
            )
        )

    return DashboardOverview(
        total_endpoints=total_endpoints,
        operational_count=operational,
        degraded_count=degraded,
        down_count=down,
        paused_count=paused,
        active_incidents_count=active_incidents,
        overall_uptime_percentage=overall_uptime,
        average_response_time_ms=avg_latency,
        endpoint_health=endpoint_health_list,
        recent_activity=activity_items,
    )


@router.get("/health", response_model=list[EndpointHealthSummary])
async def get_health_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve fast health summary for all monitored endpoints."""
    overview = await get_overview(current_user, session)
    return overview.endpoint_health


@router.get("/activity", response_model=list[ActivityItem])
async def get_activity(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve recent operational activity."""
    overview = await get_overview(current_user, session)
    return overview.recent_activity
