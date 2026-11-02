"""Notification channels and deliveries schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    channel_type: str = Field(..., pattern="^(email|webhook)$")
    destination: str = Field(..., min_length=3, max_length=1024)
    configuration: dict[str, Any] | None = None
    is_enabled: bool = True


class NotificationChannelUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    destination: str | None = Field(None, min_length=3, max_length=1024)
    configuration: dict[str, Any] | None = None
    is_enabled: bool | None = None


class NotificationChannelResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    channel_type: str
    destination: str
    configuration: dict[str, Any] | None = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationDeliveryResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    channel_id: uuid.UUID
    channel_name: str | None = None
    channel_type: str | None = None
    event_type: str
    delivery_status: str
    attempts: int
    last_attempt_at: datetime | None = None
    response_status: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationHistoryResponse(BaseModel):
    items: list[NotificationDeliveryResponse]
    total: int
    page: int
    per_page: int
