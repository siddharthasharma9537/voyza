"""
app/tasks/jobs/notifications.py
────────────────────────────────
Celery tasks for all notification-related async work.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import and_, select

from app.db.base import AsyncSessionLocal
from app.models.models import Booking, BookingStatus, Car, User
from app.services import notification_service

logger = logging.getLogger(__name__)


def _run(coro):
    """Run async coroutine from sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_task(self, booking_id: str):
    """
    Called immediately after payment is captured.
    Sends SMS + push to customer and owner.
    """
    async def _inner():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Booking, Car, User)
                .join(Car,  Car.id  == Booking.vehicle_id)
                .join(User, User.id == Booking.customer_id)
                .where(Booking.id == booking_id)
            )
            row = result.one_or_none()
            if not row:
                logger.error("booking_not_found_for_notification", booking_id=booking_id)
                return

            booking, car, customer = row.Booking, row.Car, row.User

            # Get owner
            owner_result = await db.execute(select(User).where(User.id == booking.owner_id))
            owner = owner_result.scalar_one_or_none()
            if not owner:
                return

            await notification_service.notify_booking_confirmed(
                customer_phone=customer.phone,
                customer_id=customer.id,
                owner_phone=owner.phone,
                owner_id=owner.id,
                booking_id=booking_id,
                car_name=f"{car.make} {car.model}",
                pickup_time=booking.pickup_time,
                total_amount=booking.total_amount,
            )

    try:
        _run(_inner())
    except Exception as exc:
        logger.error("confirmation_task_failed", booking_id=booking_id, error=str(exc))
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def send_pickup_reminder_task(self, booking_id: str, hours_before: int):
    """
    Scheduled by send_booking_confirmation_task at:
      - 24h before pickup (hours_before=24)
      - 2h before pickup  (hours_before=2)
    """
    async def _inner():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Booking, Car, User)
                .join(Car,  Car.id  == Booking.vehicle_id)
                .join(User, User.id == Booking.customer_id)
                .where(Booking.id == booking_id)
            )
            row = result.one_or_none()
            if not row:
                return

            booking, car, customer = row.Booking, row.Car, row.User

            # Skip if booking was cancelled
            if booking.status == BookingStatus.CANCELLED:
                return

            await notification_service.notify_pickup_reminder(
                customer_phone=customer.phone,
                customer_id=customer.id,
                booking_id=booking_id,
                car_name=f"{car.make} {car.model}",
                pickup_address=booking.pickup_address,
                pickup_time=booking.pickup_time,
            )

    try:
        _run(_inner())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def check_pickup_reminders():
    """
    Beat task — runs every hour.
    Finds bookings with pickup in ~24h or ~2h that haven't had reminders sent.

    In production: use a sent_reminders table or Redis set to track
    which reminders have already been sent.
    """
    async def _inner():
        now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            # Bookings with pickup in 23-25h window (24h reminder)
            reminder_24h = await db.execute(
                select(Booking).where(
                    and_(
                        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
                        Booking.pickup_time >= now + timedelta(hours=23),
                        Booking.pickup_time <= now + timedelta(hours=25),
                    )
                )
            )
            for booking in reminder_24h.scalars().all():
                send_pickup_reminder_task.delay(booking.id, hours_before=24)

            # Bookings with pickup in 1.5-2.5h window (2h reminder)
            reminder_2h = await db.execute(
                select(Booking).where(
                    and_(
                        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.ACTIVE]),
                        Booking.pickup_time >= now + timedelta(hours=1, minutes=30),
                        Booking.pickup_time <= now + timedelta(hours=2, minutes=30),
                    )
                )
            )
            for booking in reminder_2h.scalars().all():
                send_pickup_reminder_task.delay(booking.id, hours_before=2)

    _run(_inner())


@shared_task
def send_cancellation_notification_task(
    booking_id: str,
    customer_phone: str,
    customer_id: str,
    car_name: str,
    refund_amount: int | None,
):
    async def _inner():
        await notification_service.notify_booking_cancelled(
            customer_phone=customer_phone,
            customer_id=customer_id,
            booking_id=booking_id,
            car_name=car_name,
            refund_amount=refund_amount,
        )
    _run(_inner())
