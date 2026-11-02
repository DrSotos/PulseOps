"""Notification channels and delivery history REST API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import PaginationParams, get_current_user
from app.api.v1.schemas.notifications import (
    NotificationChannelCreate,
    NotificationChannelResponse,
    NotificationChannelUpdate,
    NotificationDeliveryResponse,
    NotificationHistoryResponse,
)
from app.db.session import get_db
from app.models.notification import NotificationChannel, NotificationDelivery
from app.models.user import User
from app.services.notifications.email_sender import send_email_notification
from app.services.notifications.webhook_sender import send_webhook_notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/channels", response_model=list[NotificationChannelResponse])
async def list_channels(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieve all notification channels configured by current user."""
    stmt = (
        select(NotificationChannel)
        .where(NotificationChannel.user_id == current_user.id)
        .order_by(desc(NotificationChannel.created_at))
    )
    res = await session.execute(stmt)
    return [NotificationChannelResponse.model_validate(c) for c in res.scalars().all()]


@router.post("/channels", response_model=NotificationChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: NotificationChannelCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new notification channel (email or webhook)."""
    channel = NotificationChannel(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name=payload.name,
        channel_type=payload.channel_type.lower(),
        destination=payload.destination.strip(),
        configuration=payload.configuration,
        is_enabled=payload.is_enabled,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return NotificationChannelResponse.model_validate(channel)


@router.patch("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def update_channel(
    channel_id: uuid.UUID,
    payload: NotificationChannelUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Modify settings for a notification channel."""
    stmt = select(NotificationChannel).where(
        and_(
            NotificationChannel.id == channel_id,
            NotificationChannel.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    channel = res.scalars().first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(channel, field, val)

    await session.commit()
    await session.refresh(channel)
    return NotificationChannelResponse.model_validate(channel)


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a notification channel."""
    stmt = select(NotificationChannel).where(
        and_(
            NotificationChannel.id == channel_id,
            NotificationChannel.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    channel = res.scalars().first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    await session.delete(channel)
    await session.commit()


@router.post("/channels/{channel_id}/test")
async def test_channel(
    channel_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Trigger a live test alert to verify delivery configuration."""
    stmt = select(NotificationChannel).where(
        and_(
            NotificationChannel.id == channel_id,
            NotificationChannel.user_id == current_user.id,
        )
    )
    res = await session.execute(stmt)
    channel = res.scalars().first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    if channel.channel_type == "email":
        success, err = await send_email_notification(
            to_email=channel.destination,
            subject="[PulseOps] Test Notification",
            html_body="<p>This is a live test notification from your PulseOps monitoring system.</p>",
            text_body="This is a live test notification from your PulseOps monitoring system.",
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Email test dispatch failed: {err}",
            )
        return {"success": True, "message": "Email test dispatched successfully."}

    elif channel.channel_type == "webhook":
        test_payload = {
            "event_type": "test_notification",
            "message": "PulseOps channel test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }
        success, code, err = await send_webhook_notification(
            url=channel.destination,
            payload=test_payload,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Webhook delivery failed (HTTP {code}): {err}",
            )
        return {"success": True, "status_code": code, "message": "Webhook test delivered successfully."}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported channel type.")


@router.get("/history", response_model=NotificationHistoryResponse)
async def list_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
):
    """Retrieve audit log of all notification delivery attempts."""
    count_stmt = (
        select(func.count(NotificationDelivery.id))
        .join(NotificationChannel, NotificationDelivery.channel_id == NotificationChannel.id)
        .where(NotificationChannel.user_id == current_user.id)
    )
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    stmt = (
        select(NotificationDelivery, NotificationChannel.name, NotificationChannel.channel_type)
        .join(NotificationChannel, NotificationDelivery.channel_id == NotificationChannel.id)
        .where(NotificationChannel.user_id == current_user.id)
        .order_by(desc(NotificationDelivery.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    res = await session.execute(stmt)
    rows = res.all()

    items: list[NotificationDeliveryResponse] = []
    for d, c_name, c_type in rows:
        resp = NotificationDeliveryResponse.model_validate(d)
        resp.channel_name = c_name
        resp.channel_type = c_type
        items.append(resp)

    return NotificationHistoryResponse(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
    )
