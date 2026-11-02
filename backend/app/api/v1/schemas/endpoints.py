"""Monitored endpoint Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EndpointCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=2048)
    http_method: str = Field("GET", pattern="^(GET|HEAD|POST)$")
    monitoring_interval: int = Field(60, ge=30, le=900)
    timeout: int = Field(10, ge=1, le=30)
    expected_status_codes: list[int] = Field(default_factory=lambda: [200])
    performance_threshold_ms: int | None = Field(None, ge=10, le=60000)
    custom_headers: dict[str, str] | None = None
    request_body: str | None = None
    expected_content: str | None = Field(None, max_length=1024)
    expected_content_type: str | None = Field(None, max_length=255)
    is_active: bool = True

    @field_validator("expected_status_codes")
    @classmethod
    def validate_statuses(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("Must specify at least one expected status code.")
        for code in v:
            if not (100 <= code <= 599):
                raise ValueError(f"Invalid HTTP status code {code}.")
        return v


class EndpointUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    url: str | None = Field(None, max_length=2048)
    http_method: str | None = Field(None, pattern="^(GET|HEAD|POST)$")
    monitoring_interval: int | None = Field(None, ge=30, le=900)
    timeout: int | None = Field(None, ge=1, le=30)
    expected_status_codes: list[int] | None = None
    performance_threshold_ms: int | None = Field(None, ge=10, le=60000)
    custom_headers: dict[str, str] | None = None
    request_body: str | None = None
    expected_content: str | None = Field(None, max_length=1024)
    expected_content_type: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class EndpointResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    url: str
    http_method: str
    monitoring_interval: int
    timeout: int
    expected_status_codes: list[int]
    performance_threshold_ms: int | None = None
    custom_headers: dict[str, Any] | None = None
    request_body: str | None = None
    expected_content: str | None = None
    expected_content_type: str | None = None
    is_active: bool
    last_checked_at: datetime | None = None
    last_success_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    current_status: str = "unknown"
    latest_response_time_ms: float | None = None
    uptime_percentage: float | None = None

    model_config = ConfigDict(from_attributes=True)


class EndpointListResponse(BaseModel):
    items: list[EndpointResponse]
    total: int
    page: int
    per_page: int
