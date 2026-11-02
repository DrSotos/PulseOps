"""MonitoringCheck model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.endpoint import MonitoredEndpoint


class MonitoringCheck(Base):
    """Result of a single health-check probe against an endpoint."""

    __tablename__ = "monitoring_checks"
    __table_args__ = (
        # Composite index for efficient time-range queries per endpoint
        Index("ix_monitoring_checks_endpoint_id_created_at", "endpoint_id", "created_at"),
        # Composite index for fast uptime calculations
        Index("ix_monitoring_checks_endpoint_id_is_successful", "endpoint_id", "is_successful"),
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
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_successful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    response_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    endpoint: Mapped["MonitoredEndpoint"] = relationship(
        "MonitoredEndpoint", back_populates="checks"
    )
