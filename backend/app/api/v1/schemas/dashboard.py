"""Dashboard overview and telemetry aggregation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class EndpointHealthSummary(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    http_method: str
    status: str
    latest_response_time_ms: float | None = None
    uptime_percentage: float
    last_checked_at: datetime | None = None


class ActivityItem(BaseModel):
    id: str
    type: str  # check, incident_opened, incident_resolved
    title: str
    description: str
    timestamp: datetime
    severity: str | None = None


class DashboardOverview(BaseModel):
    total_endpoints: int
    operational_count: int
    degraded_count: int
    down_count: int
    paused_count: int
    active_incidents_count: int
    overall_uptime_percentage: float
    average_response_time_ms: float | None = None
    endpoint_health: list[EndpointHealthSummary]
    recent_activity: list[ActivityItem]
