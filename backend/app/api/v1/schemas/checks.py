"""Monitoring check response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CheckResponse(BaseModel):
    id: uuid.UUID
    endpoint_id: uuid.UUID
    started_at: datetime
    completed_at: datetime
    response_time_ms: float | None = None
    status_code: int | None = None
    is_successful: bool
    failure_type: str | None = None
    error_message: str | None = None
    response_size_bytes: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckListResponse(BaseModel):
    items: list[CheckResponse]
    total: int
    page: int
    per_page: int


class UptimeResponse(BaseModel):
    endpoint_id: str
    period: str
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float
    first_check_at: str | None = None
    last_check_at: str | None = None


class LatencyResponse(BaseModel):
    endpoint_id: str
    period: str
    sample_count: int
    avg_ms: float | None = None
    min_ms: float | None = None
    max_ms: float | None = None
    p50_ms: float | None = None
    p90_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None


class EndpointStatistics(BaseModel):
    endpoint_id: str
    period: str
    uptime: UptimeResponse
    latency: LatencyResponse
    current_status: str
    last_check_at: datetime | None = None
    last_success_at: datetime | None = None
