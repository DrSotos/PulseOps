"""Monitored Endpoints REST API endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import PaginationParams, get_current_user
from app.api.v1.schemas.checks import (
    CheckListResponse,
    CheckResponse,
    EndpointStatistics,
    LatencyResponse,
    UptimeResponse,
)
from app.api.v1.schemas.endpoints import (
    EndpointCreate,
    EndpointListResponse,
    EndpointResponse,
    EndpointUpdate,
)
from app.db.session import get_db
from app.models.check import MonitoringCheck
from app.models.endpoint import MonitoredEndpoint
from app.models.user import User
from app.services.incidents.detector import process_check_result
from app.services.monitoring.checker import execute_check
from app.services.statistics.calculator import (
    calculate_latency,
    calculate_uptime,
    get_endpoint_status,
)
from app.utils.url_validator import URLValidationError, validate_url

router = APIRouter(prefix="/endpoints", tags=["Monitored Endpoints"])


async def _enrich_endpoint(session: AsyncSession, ep: MonitoredEndpoint) -> EndpointResponse:
    status_str = await get_endpoint_status(session, ep)
    uptime_data = await calculate_uptime(session, ep.id, "24h")

    # Fetch latest response time
    latest_stmt = (
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
    latest_res = await session.execute(latest_stmt)
    latest_val = latest_res.scalar_one_or_none()

    resp = EndpointResponse.model_validate(ep)
    resp.current_status = status_str
    resp.uptime_percentage = uptime_data.get("uptime_percentage")
    resp.latest_response_time_ms = latest_val
    return resp


@router.get("", response_model=EndpointListResponse)
async def list_endpoints(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    search: str | None = Query(None, description="Search by name or URL"),
    is_active: bool | None = Query(None, description="Filter by active status"),
):
    """List monitored endpoints belonging to the authenticated user."""
    conditions = [MonitoredEndpoint.user_id == current_user.id]

    if search:
        search_filter = f"%{search.strip()}%"
        conditions.append(
            (MonitoredEndpoint.name.ilike(search_filter))
            | (MonitoredEndpoint.url.ilike(search_filter))
        )
    if is_active is not None:
        conditions.append(MonitoredEndpoint.is_active == is_active)

    # Count total
    count_stmt = select(func.count(MonitoredEndpoint.id)).where(and_(*conditions))
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Query items
    query = (
        select(MonitoredEndpoint)
        .where(and_(*conditions))
        .order_by(desc(MonitoredEndpoint.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    res = await session.execute(query)
    endpoints = res.scalars().all()

    enriched_items = [await _enrich_endpoint(session, ep) for ep in endpoints]

    return EndpointListResponse(
        items=enriched_items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


@router.post("", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    payload: EndpointCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new monitored endpoint."""
    try:
        validated_url = validate_url(payload.url)
    except URLValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Security check failed for URL: {e}",
        )

    endpoint = MonitoredEndpoint(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=payload.name,
        url=validated_url,
        http_method=payload.http_method.upper(),
        monitoring_interval=payload.monitoring_interval,
        timeout=payload.timeout,
        expected_status_codes=payload.expected_status_codes,
        performance_threshold_ms=payload.performance_threshold_ms,
        custom_headers=payload.custom_headers,
        request_body=payload.request_body,
        expected_content=payload.expected_content,
        expected_content_type=payload.expected_content_type,
        is_active=payload.is_active,
    )
    session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)

    return await _enrich_endpoint(session, endpoint)


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve details for a specific endpoint."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    return await _enrich_endpoint(session, endpoint)


@router.patch("/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(
    endpoint_id: uuid.UUID,
    payload: EndpointUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Update monitoring parameters for an existing endpoint."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    update_data = payload.model_dump(exclude_unset=True)

    if update_data.get("url"):
        try:
            update_data["url"] = validate_url(update_data["url"])
        except URLValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Security check failed for URL: {e}",
            )

    for field, val in update_data.items():
        setattr(endpoint, field, val)

    await session.commit()
    await session.refresh(endpoint)
    return await _enrich_endpoint(session, endpoint)


@router.delete("/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_endpoint(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove an endpoint and cascade-delete its historical checks and incidents."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    await session.delete(endpoint)
    await session.commit()


@router.post("/{endpoint_id}/pause", response_model=EndpointResponse)
async def pause_endpoint(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Pause automated monitoring checks for this endpoint."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    endpoint.is_active = False
    await session.commit()
    await session.refresh(endpoint)
    return await _enrich_endpoint(session, endpoint)


@router.post("/{endpoint_id}/resume", response_model=EndpointResponse)
async def resume_endpoint(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Resume automated monitoring checks for this endpoint."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    endpoint.is_active = True
    await session.commit()
    await session.refresh(endpoint)
    return await _enrich_endpoint(session, endpoint)


@router.post("/{endpoint_id}/check", response_model=CheckResponse)
async def manual_check(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger an immediate real health check on-demand."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    check = await execute_check(endpoint)
    session.add(check)

    endpoint.last_checked_at = check.completed_at
    if check.is_successful:
        endpoint.last_success_at = check.completed_at

    await session.commit()
    await session.refresh(check)

    # Process incident evaluation asynchronously
    await process_check_result(session, endpoint, check)

    return check


@router.get("/{endpoint_id}/checks", response_model=CheckListResponse)
async def list_endpoint_checks(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
):
    """Retrieve historical check executions for an endpoint."""
    # Verify ownership
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    count_stmt = select(func.count(MonitoringCheck.id)).where(
        MonitoringCheck.endpoint_id == endpoint_id
    )
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    checks_stmt = (
        select(MonitoringCheck)
        .where(MonitoringCheck.endpoint_id == endpoint_id)
        .order_by(desc(MonitoringCheck.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    c_res = await session.execute(checks_stmt)
    checks = c_res.scalars().all()

    return CheckListResponse(
        items=[CheckResponse.model_validate(c) for c in checks],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )


@router.get("/{endpoint_id}/statistics", response_model=EndpointStatistics)
async def get_endpoint_statistics(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
):
    """Retrieve combined uptime, response time, and percentile distribution statistics."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    endpoint = res.scalars().first()
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    uptime_dict = await calculate_uptime(session, endpoint_id, period)
    latency_dict = await calculate_latency(session, endpoint_id, period)
    status_str = await get_endpoint_status(session, endpoint)

    return EndpointStatistics(
        endpoint_id=str(endpoint_id),
        period=period,
        uptime=UptimeResponse(**uptime_dict),
        latency=LatencyResponse(**latency_dict),
        current_status=status_str,
        last_check_at=endpoint.last_checked_at,
        last_success_at=endpoint.last_success_at,
    )


@router.get("/{endpoint_id}/uptime", response_model=UptimeResponse)
async def get_endpoint_uptime(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
):
    """Retrieve uptime statistics specifically."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    uptime_dict = await calculate_uptime(session, endpoint_id, period)
    return UptimeResponse(**uptime_dict)


@router.get("/{endpoint_id}/latency", response_model=LatencyResponse)
async def get_endpoint_latency(
    endpoint_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
):
    """Retrieve latency and percentile distribution metrics."""
    stmt = select(MonitoredEndpoint).where(
        and_(
            MonitoredEndpoint.id == endpoint_id,
            MonitoredEndpoint.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found.")

    latency_dict = await calculate_latency(session, endpoint_id, period)
    return LatencyResponse(**latency_dict)
