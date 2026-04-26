"""
app/models/notification.py
──────────────────────────
Notification model for tracking email, SMS, and push notifications.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(str, enum.Enum):
    """Notification types"""
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_CANCELLED = "booking_cancelled"
    PICKUP_REMINDER_24H = "pickup_reminder_24h"
    PICKUP_REMINDER_2H = "pickup_reminder_2h"
    RETURN_REMINDER = "return_reminder"
    REFUND_PROCESSED = "refund_processed"
    REFUND_INITIATED = "refund_initiated"
    OTP_VERIFICATION = "otp_verification"
    SUPPORT_RESPONSE = "support_response"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class Notification(Base):
    """
    Tracks all notifications sent to users.
    Allows for audit trail and retry logic for failed notifications.
    """
    __tablename__ = "notifications"
    __allow_unmapped__ = True

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    booking_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("bookings.id"), nullable=True)

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, values_callable=lambda x: [e.value for e in x], name="notificationtype"),
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, values_callable=lambda x: [e.value for e in x], name="notificationchannel"),
        nullable=False,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, values_callable=lambda x: [e.value for e in x], name="notificationstatus"),
        default=NotificationStatus.PENDING,
        nullable=False,
    )

    # Recipient information (could be email, phone, or push token)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)

    # Email-specific fields
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tracking fields
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    user: "User" = relationship("User", back_populates="notifications")
    booking: "Booking | None" = relationship("Booking", foreign_keys=[booking_id])

    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_booking_id", "booking_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_channel", "channel"),
        Index("ix_notifications_type", "notification_type"),
        Index("ix_notifications_created_at", "created_at"),
    )
