"""Incident model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.endpoint import MonitoredEndpoint
    from app.models.incident_event import IncidentEvent
    from app.models.notification import NotificationDelivery


class Incident(Base):
    """An incident tied to a monitored endpoint (outage, latency spike, etc.)."""

    __tablename__ = "incidents"
    __table_args__ = (
        # Find active incidents for a given endpoint quickly
        Index("ix_incidents_endpoint_id_status", "endpoint_id", "status"),
        # List incidents filtered by status
        Index("ix_incidents_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("monitored_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="outage | high_latency | unexpected_status | response_validation | ssl_error",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="low | medium | high | critical",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="detected",
        comment="detected | open | acknowledged | resolved",
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    endpoint: Mapped["MonitoredEndpoint"] = relationship(
        "MonitoredEndpoint", back_populates="incidents"
    )
    events: Mapped[list["IncidentEvent"]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentEvent.created_at",
    )
    notification_deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        "NotificationDelivery",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
