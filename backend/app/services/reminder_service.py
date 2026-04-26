"""
app/services/reminder_service.py
─────────────────────────────────
Reminder scheduling for pre-pickup notifications.

Reminders are sent:
- 24 hours before pickup
- 2 hours before pickup

Can be triggered by:
- Celery beat scheduler (recurring task)
- Manual endpoint call
- APScheduler or similar background job runner
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Booking, BookingStatus
from app.services.notification_service import notify_pickup_reminder


# ── Reminder thresholds (in hours) ────────────────────────────────────────────

REMINDER_THRESHOLDS = [
    {"hours": 24, "name": "24h_before"},
    {"hours": 2, "name": "2h_before"},
]


# ── Send pending reminders ─────────────────────────────────────────────────────

async def send_pending_reminders(db: AsyncSession) -> dict:
    """
    Scan for bookings that need reminders sent.
    Called by background job scheduler (Celery beat, APScheduler, cron, etc.)

    Returns count of reminders sent.
    """
    now = datetime.now(timezone.utc)
    reminders_sent = {"24h": 0, "2h": 0}

    for threshold in REMINDER_THRESHOLDS:
        hours = threshold["hours"]
        name = threshold["name"]

        # Find bookings where pickup is approximately N hours away
        # We use a 30-minute window to avoid sending multiple times
        target_time = now + timedelta(hours=hours)
        window_start = target_time - timedelta(minutes=30)
        window_end = target_time + timedelta(minutes=30)

        result = await db.execute(
            select(Booking)
            .where(
                and_(
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.pickup_time >= window_start,
                    Booking.pickup_time <= window_end,
                )
            )
        )
        bookings = result.scalars().all()

        for booking in bookings:
            try:
                # Get customer and vehicle info
                from sqlalchemy import select as sqlselect
                from app.models.models import User, Vehicle

                customer_result = await db.execute(
                    sqlselect(User).where(User.id == booking.customer_id)
                )
                customer = customer_result.scalar_one_or_none()

                vehicle_result = await db.execute(
                    sqlselect(Vehicle).where(Vehicle.id == booking.vehicle_id)
                )
                vehicle = vehicle_result.scalar_one_or_none()

                if customer and vehicle:
                    # Send reminder notification
                    await notify_pickup_reminder(
                        customer_phone=customer.phone,
                        customer_id=customer.id,
                        booking_id=booking.id,
                        car_name=f"{vehicle.make} {vehicle.model}",
                        pickup_address=booking.pickup_address,
                        pickup_time=booking.pickup_time,
                    )
                    reminders_sent[f"{hours}h"] += 1
            except Exception as e:
                # Log error but continue with next booking
                print(f"Error sending reminder for booking {booking.id}: {str(e)}")

    return reminders_sent


# ── Get upcoming reminders for a customer ──────────────────────────────────────

async def get_upcoming_reminders(customer_id: str, db: AsyncSession) -> list[dict]:
    """Get upcoming reminders for the customer's bookings."""
    now = datetime.now(timezone.utc)

    # Get all confirmed bookings in the future
    result = await db.execute(
        select(Booking)
        .where(
            and_(
                Booking.customer_id == customer_id,
                Booking.status == BookingStatus.CONFIRMED,
                Booking.pickup_time > now,
            )
        )
        .order_by(Booking.pickup_time)
    )
    bookings = result.scalars().all()

    reminders = []
    for booking in bookings:
        hours_until = (booking.pickup_time - now).total_seconds() / 3600

        # Determine which reminders are pending
        reminder_info = {
            "booking_id": booking.id,
            "pickup_time": booking.pickup_time.isoformat(),
            "hours_until_pickup": round(hours_until, 1),
            "reminders_pending": [],
        }

        for threshold in REMINDER_THRESHOLDS:
            threshold_hours = threshold["hours"]
            # Consider pending if within +/- 1 hour of threshold
            if abs(hours_until - threshold_hours) < 1:
                reminder_info["reminders_pending"].append(f"{threshold_hours}h")

        if reminder_info["reminders_pending"]:
            reminders.append(reminder_info)

    return reminders
