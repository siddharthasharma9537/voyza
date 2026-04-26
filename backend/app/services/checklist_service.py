"""
app/services/checklist_service.py
──────────────────────────────────
Checklist management for pre-pickup and post-return inspections.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Booking, BookingStatus, ChecklistItem, ChecklistType


# ── Initialize checklists for a booking ────────────────────────────────────────

PRE_PICKUP_ITEMS = [
    {"id": "fuel", "label": "Fill fuel to full tank", "required": True},
    {"id": "wash", "label": "Wash and clean vehicle", "required": True},
    {"id": "interior", "label": "Clean interior (seats, floor, dashboard)", "required": True},
    {"id": "documents", "label": "Prepare RC, insurance, key, spare key", "required": True},
    {"id": "photos", "label": "Take vehicle condition photos", "required": True},
    {"id": "odometer", "label": "Note current odometer reading", "required": True},
    {"id": "inspect", "label": "Inspect for dents, scratches, damage", "required": True},
]

POST_RETURN_ITEMS = [
    {"id": "fuel-return", "label": "Check fuel level (should be full)", "required": True},
    {"id": "condition", "label": "Check vehicle condition for damage", "required": True},
    {"id": "mileage", "label": "Record odometer reading", "required": True},
    {"id": "interior-return", "label": "Inspect interior condition", "required": True},
    {"id": "photos-return", "label": "Take return condition photos", "required": True},
    {"id": "documents-return", "label": "Collect all documents back", "required": True},
]


async def initialize_checklists(booking_id: str, db: AsyncSession) -> None:
    """
    Create pre-pickup and post-return checklist items for a new booking.
    Called when booking is confirmed.
    """
    # Create pre-pickup checklist
    for item in PRE_PICKUP_ITEMS:
        checklist_item = ChecklistItem(
            booking_id=booking_id,
            checklist_type=ChecklistType.PRE_PICKUP,
            item_id=item["id"],
            item_label=item["label"],
            completed=False,
            required=item["required"],
        )
        db.add(checklist_item)

    # Create post-return checklist
    for item in POST_RETURN_ITEMS:
        checklist_item = ChecklistItem(
            booking_id=booking_id,
            checklist_type=ChecklistType.POST_RETURN,
            item_id=item["id"],
            item_label=item["label"],
            completed=False,
            required=item["required"],
        )
        db.add(checklist_item)


# ── Update checklist item ──────────────────────────────────────────────────────

async def update_checklist_item(
    booking_id: str,
    checklist_type: ChecklistType,
    item_id: str,
    completed: bool,
    db: AsyncSession,
) -> ChecklistItem:
    """Mark a checklist item as completed or incomplete."""
    result = await db.execute(
        select(ChecklistItem).where(
            and_(
                ChecklistItem.booking_id == booking_id,
                ChecklistItem.checklist_type == checklist_type,
                ChecklistItem.item_id == item_id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(404, "Checklist item not found")

    item.completed = completed
    if completed:
        item.completed_at = datetime.now(timezone.utc)

    return item


# ── Get checklist for a booking ────────────────────────────────────────────────

async def get_checklist(
    booking_id: str,
    checklist_type: ChecklistType,
    db: AsyncSession,
) -> list[dict]:
    """Get all checklist items for a specific checklist."""
    result = await db.execute(
        select(ChecklistItem).where(
            and_(
                ChecklistItem.booking_id == booking_id,
                ChecklistItem.checklist_type == checklist_type,
            )
        )
    )
    items = result.scalars().all()

    return [
        {
            "id": item.item_id,
            "label": item.item_label,
            "completed": item.completed,
            "required": item.required,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        }
        for item in items
    ]


# ── Batch update checklist items ───────────────────────────────────────────────

async def batch_update_checklist(
    booking_id: str,
    checklist_type: ChecklistType,
    updates: list[dict],  # [{"item_id": "fuel", "completed": True}, ...]
    db: AsyncSession,
) -> list[dict]:
    """Update multiple checklist items at once."""
    for update in updates:
        await update_checklist_item(
            booking_id=booking_id,
            checklist_type=checklist_type,
            item_id=update["item_id"],
            completed=update.get("completed", False),
            db=db,
        )

    return await get_checklist(booking_id, checklist_type, db)


# ── Check if all required items are completed ──────────────────────────────────

async def is_checklist_complete(
    booking_id: str,
    checklist_type: ChecklistType,
    db: AsyncSession,
) -> bool:
    """Check if all required items in the checklist are completed."""
    result = await db.execute(
        select(ChecklistItem).where(
            and_(
                ChecklistItem.booking_id == booking_id,
                ChecklistItem.checklist_type == checklist_type,
                ChecklistItem.required.is_(True),
            )
        )
    )
    items = result.scalars().all()

    if not items:
        return False

    return all(item.completed for item in items)
