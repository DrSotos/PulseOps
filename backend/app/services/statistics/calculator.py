"""Analytics calculation engine: response times, percentile distributions, and uptime metrics."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.check import MonitoringCheck
from app.models.endpoint import MonitoredEndpoint

logger = get_logger(__name__)


def parse_period(period: str) -> timedelta:
    periods = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }
    return periods.get(period.lower(), timedelta(hours=24))


def _calculate_percentile(sorted_data: list[float], percentile: float) -> float | None:
    """Calculate percentile from a sorted list of numeric response times."""
    if not sorted_data:
        return None
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    rank = (percentile / 100.0) * (n - 1)
    lower = int(rank)
    upper = min(lower + 1, n - 1)
    weight = rank - lower
    val = sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight
    return round(val, 2)


async def calculate_uptime(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    period: str = "24h",
) -> dict[str, Any]:
    """Calculate availability uptime metrics for an endpoint over the selected period."""
    delta = parse_period(period)
    cutoff = datetime.now(UTC) - delta

    stmt = select(
        func.count(MonitoringCheck.id).label("total"),
        func.count(case((MonitoringCheck.is_successful == True, 1))).label("successful"),
        func.count(case((MonitoringCheck.is_successful == False, 1))).label("failed"),
        func.min(MonitoringCheck.created_at).label("first_check"),
        func.max(MonitoringCheck.created_at).label("last_check"),
    ).where(
        and_(
            MonitoringCheck.endpoint_id == endpoint_id,
            MonitoringCheck.created_at >= cutoff,
            MonitoringCheck.failure_type != "internal_error",
        )
    )

    res = await session.execute(stmt)
    row = res.one()

    total = row.total or 0
    successful = row.successful or 0
    failed = row.failed or 0
    uptime_pct = round((successful / total * 100.0), 2) if total > 0 else 100.0

    return {
        "endpoint_id": str(endpoint_id),
        "period": period,
        "total_checks": total,
        "successful_checks": successful,
        "failed_checks": failed,
        "uptime_percentage": uptime_pct,
        "first_check_at": row.first_check.isoformat() if row.first_check else None,
        "last_check_at": row.last_check.isoformat() if row.last_check else None,
    }


async def calculate_latency(
    session: AsyncSession,
    endpoint_id: uuid.UUID,
    period: str = "24h",
) -> dict[str, Any]:
    """Calculate latency statistics including P50, P90, P95, and P99 percentiles."""
    delta = parse_period(period)
    cutoff = datetime.now(UTC) - delta

    stmt_agg = select(
        func.count(MonitoringCheck.id).label("sample_count"),
        func.avg(MonitoringCheck.response_time_ms).label("avg_ms"),
        func.min(MonitoringCheck.response_time_ms).label("min_ms"),
        func.max(MonitoringCheck.response_time_ms).label("max_ms"),
    ).where(
        and_(
            MonitoringCheck.endpoint_id == endpoint_id,
            MonitoringCheck.created_at >= cutoff,
            MonitoringCheck.response_time_ms.isnot(None),
        )
    )

    agg_res = await session.execute(stmt_agg)
    agg_row = agg_res.one()

    sample_count = agg_row.sample_count or 0
    avg_ms = round(agg_row.avg_ms, 2) if agg_row.avg_ms else None
    min_ms = round(agg_row.min_ms, 2) if agg_row.min_ms else None
    max_ms = round(agg_row.max_ms, 2) if agg_row.max_ms else None

    # Fetch values for percentile distribution calculation
    p50_ms = p90_ms = p95_ms = p99_ms = None
    if sample_count > 0:
        times_stmt = (
            select(MonitoringCheck.response_time_ms)
            .where(
                and_(
                    MonitoringCheck.endpoint_id == endpoint_id,
                    MonitoringCheck.created_at >= cutoff,
                    MonitoringCheck.response_time_ms.isnot(None),
                )
            )
            .order_by(MonitoringCheck.response_time_ms)
        )
        times_res = await session.execute(times_stmt)
        times = [float(r[0]) for r in times_res.all()]

        p50_ms = _calculate_percentile(times, 50)
        p90_ms = _calculate_percentile(times, 90)
        p95_ms = _calculate_percentile(times, 95)
        p99_ms = _calculate_percentile(times, 99)

    return {
        "endpoint_id": str(endpoint_id),
        "period": period,
        "sample_count": sample_count,
        "avg_ms": avg_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "p50_ms": p50_ms,
        "p90_ms": p90_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
    }


async def get_endpoint_status(
    session: AsyncSession,
    endpoint: MonitoredEndpoint,
) -> str:
    """Classify current real-time health status of an endpoint.

    Possible states:
    - 'paused'
    - 'unknown'
    - 'operational'
    - 'degraded'
    - 'down'
    """
    if not endpoint.is_active:
        return "paused"

    stmt = (
        select(MonitoringCheck)
        .where(MonitoringCheck.endpoint_id == endpoint.id)
        .order_by(MonitoringCheck.created_at.desc())
        .limit(3)
    )
    res = await session.execute(stmt)
    recent = list(res.scalars().all())

    if not recent:
        return "unknown"

    latest = recent[0]
    if latest.is_successful:
        if latest.failure_type == "performance_threshold":
            return "degraded"
        return "operational"

    if all(not c.is_successful for c in recent):
        return "down"

    return "degraded"
