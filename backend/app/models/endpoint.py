"""MonitoredEndpoint model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.check import MonitoringCheck
    from app.models.incident import Incident
    from app.models.user import User


class MonitoredEndpoint(Base):
    """An HTTP endpoint that is periodically monitored."""

    __tablename__ = "monitored_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), default="GET")
    monitoring_interval: Mapped[int] = mapped_column(
        Integer, default=60, comment="Monitoring interval in seconds"
    )
    timeout: Mapped[int] = mapped_column(
        Integer, default=10, comment="Request timeout in seconds"
    )
    expected_status_codes: Mapped[list] = mapped_column(JSONB, default=[200])
    performance_threshold_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    custom_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_content: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    expected_content_type: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="endpoints")
    checks: Mapped[list["MonitoringCheck"]] = relationship(
        "MonitoringCheck", back_populates="endpoint", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", back_populates="endpoint", cascade="all, delete-orphan"
    )
