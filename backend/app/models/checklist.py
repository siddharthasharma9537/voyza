"""
app/models/checklist.py
──────────────────────
Checklist tracking for pre-pickup and post-return vehicle inspections.

Owners must complete checklists before pickup and after return.
Each checklist item tracks whether a required task is completed.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChecklistType(str, enum.Enum):
    PRE_PICKUP = "pre_pickup"
    POST_RETURN = "post_return"


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    __allow_unmapped__ = True

    booking_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )

    checklist_type: Mapped[ChecklistType] = mapped_column(
        Enum(ChecklistType, values_callable=lambda x: [e.value for e in x], name="checklisttype"),
        nullable=False,
    )

    item_id: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "fuel", "wash", "documents"
    item_label: Mapped[str] = mapped_column(String(200), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking: "Booking" = relationship("Booking", back_populates="checklist_items")

    __table_args__ = (
        Index("ix_checklist_items_booking_id", "booking_id"),
        Index("ix_checklist_items_booking_type", "booking_id", "checklist_type"),
    )
