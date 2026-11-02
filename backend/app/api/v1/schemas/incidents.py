"""Incident and incident event schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class IncidentEventResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    event_type: str
    description: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: uuid.UUID
    endpoint_id: uuid.UUID
    endpoint_name: str | None = None
    endpoint_url: str | None = None
    incident_type: str
    severity: str
    status: str
    description: str
    started_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    duration_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
    events: list[IncidentEventResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    per_page: int
