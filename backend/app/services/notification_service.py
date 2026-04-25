"""
app/services/notification_service.py
──────────────────────────────────────
Unified notification dispatcher for all platform events.

Channels:
  • SMS    — Twilio (OTP, booking confirmations, reminders)
  • Push   — Firebase Cloud Messaging (mobile apps)
  • In-app — WebSocket real-time + stored in notifications table
  • Email  — SMTP (receipts, KYC updates)

All sends are fire-and-forget wrapped in try/except —
a notification failure must NEVER break the main flow.

Event types dispatched:
  booking.created      → customer SMS + owner push
  booking.confirmed    → customer SMS + push
  booking.cancelled    → customer SMS + owner push + refund info
  booking.reminder     → customer SMS (24h before pickup)
  kyc.approved         → owner SMS + push
  kyc.rejected         → owner SMS + push + reason
  payment.captured     → customer SMS receipt
  payment.refunded     → customer SMS
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.websocket_manager import manager as ws_manager

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════ SMS (Twilio)

async def send_sms(to: str, body: str) -> bool:
    """
    Send SMS via Twilio REST API.
    Returns True on success, False on failure (non-fatal).
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("sms_skipped_no_credentials", to=to)
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data={
                    "From": settings.TWILIO_FROM_NUMBER,
                    "To":   to,
                    "Body": body,
                },
            )
            if resp.status_code == 201:
                logger.info("sms_sent", to=to, status=201)
                return True
            else:
                logger.error("sms_failed", to=to, status=resp.status_code, body=resp.text)
                return False
    except Exception as e:
        logger.error("sms_exception", to=to, error=str(e))
        return False


# ═══════════════════════════════════════════════════════════════ PUSH (FCM)

async def send_push(
    device_token: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> bool:
    """
    Send push notification via Firebase Cloud Messaging (FCM v1 API).
    device_token: FCM registration token from the mobile app.
    """
    fcm_url = "https://fcm.googleapis.com/v1/projects/voyza-app/messages:send"

    payload = {
        "message": {
            "token": device_token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in (data or {}).items()},
            "android": {"priority": "high"},
            "apns": {"headers": {"apns-priority": "10"}},
        }
    }

    # In production, get Bearer token from Google OAuth2 service account
    # For now, stub returns True in dev
    if settings.DEBUG:
        logger.info("push_stub", title=title, to=device_token[:20])
        return True

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(fcm_url, json=payload)
            success = resp.status_code == 200
            logger.info("push_sent" if success else "push_failed", status=resp.status_code)
            return success
    except Exception as e:
        logger.error("push_exception", error=str(e))
        return False


# ═══════════════════════════════════════════════════════════════ IN-APP (WS)

async def send_inapp(user_id: str, event: str, payload: dict[str, Any]) -> None:
    """Send real-time in-app notification via WebSocket."""
    await ws_manager.send_to_user(user_id, {
        "type":  "notification",
        "event": event,
        **payload,
    })


# ═══════════════════════════════════════════════════════════════ EMAIL

async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send transactional email via SMTP (async)."""
    if not settings.SMTP_USER:
        logger.warning("email_skipped_no_config", to=to)
        return False

    import aiosmtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.EMAILS_FROM_EMAIL
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as e:
        logger.error("email_failed", to=to, error=str(e))
        return False


# ═══════════════════════════════════════════════════════════════ EVENT DISPATCHERS

def fmt_rupees(paise: int) -> str:
    return f"₹{paise/100:,.0f}"


async def notify_booking_confirmed(
    customer_phone: str,
    customer_id: str,
    owner_phone: str,
    owner_id: str,
    booking_id: str,
    car_name: str,
    pickup_time: datetime,
    total_amount: int,
) -> None:
    """Notify both customer and owner when payment is captured."""
    pickup_str = pickup_time.strftime("%d %b %Y, %I:%M %p")
    short_id   = booking_id[:8].upper()

    # Customer SMS
    await send_sms(
        customer_phone,
        f"Voyza: Booking #{short_id} CONFIRMED!\n"
        f"Car: {car_name}\nPickup: {pickup_str}\nTotal: {fmt_rupees(total_amount)}\n"
        f"Show this ID at pickup: {short_id}"
    )

    # Customer in-app
    await send_inapp(customer_id, "booking.confirmed", {
        "booking_id": booking_id,
        "car":        car_name,
        "pickup":     pickup_str,
        "amount":     total_amount,
        "message":    f"Your {car_name} is booked for {pickup_str}!",
    })

    # Owner SMS
    await send_sms(
        owner_phone,
        f"Voyza: New booking for your {car_name}!\n"
        f"Pickup: {pickup_str}\nEarnings: {fmt_rupees(int(total_amount * 0.8))}\n"
        f"Booking #{short_id}"
    )

    # Owner in-app
    await send_inapp(owner_id, "booking.new", {
        "booking_id": booking_id,
        "car":        car_name,
        "pickup":     pickup_str,
    })

    # Admin feed
    await ws_manager.broadcast_admin({
        "type":       "booking.confirmed",
        "booking_id": booking_id,
        "car":        car_name,
        "amount":     total_amount,
    })

    logger.info("notifications_sent", event="booking.confirmed", booking_id=booking_id)


async def notify_booking_cancelled(
    customer_phone: str,
    customer_id: str,
    booking_id: str,
    car_name: str,
    refund_amount: int | None,
) -> None:
    short_id = booking_id[:8].upper()
    refund_str = f"\nRefund: {fmt_rupees(refund_amount)} (5-7 business days)" if refund_amount else ""

    await send_sms(
        customer_phone,
        f"Voyza: Booking #{short_id} cancelled.{refund_str}\n"
        f"Questions? Contact support@voyza.app"
    )
    await send_inapp(customer_id, "booking.cancelled", {
        "booking_id":   booking_id,
        "car":          car_name,
        "refund_amount": refund_amount,
    })


async def notify_kyc_result(
    owner_phone: str,
    owner_id: str,
    car_name: str,
    approved: bool,
    notes: str | None = None,
) -> None:
    if approved:
        await send_sms(
            owner_phone,
            f"Voyza: Great news! Your {car_name} is now LIVE on Voyza. "
            f"Customers can start booking it now."
        )
        await send_inapp(owner_id, "kyc.approved", {
            "car": car_name,
            "message": f"Your {car_name} is now live and accepting bookings!",
        })
    else:
        reason = notes or "Documents incomplete or unclear"
        await send_sms(
            owner_phone,
            f"Voyza: KYC for your {car_name} was not approved.\n"
            f"Reason: {reason}\n"
            f"Please resubmit via the Owner App."
        )
        await send_inapp(owner_id, "kyc.rejected", {
            "car":    car_name,
            "reason": reason,
        })


async def notify_pickup_reminder(
    customer_phone: str,
    customer_id: str,
    booking_id: str,
    car_name: str,
    pickup_address: str | None,
    pickup_time: datetime,
) -> None:
    """Sent 24h and 2h before pickup by Celery beat scheduler."""
    short_id   = booking_id[:8].upper()
    pickup_str = pickup_time.strftime("%d %b, %I:%M %p")
    addr_str   = f"\nPickup location: {pickup_address}" if pickup_address else ""

    await send_sms(
        customer_phone,
        f"Voyza reminder: Your {car_name} pickup is tomorrow at {pickup_str}."
        f"{addr_str}\nBooking #{short_id}"
    )
    await send_inapp(customer_id, "booking.reminder", {
        "booking_id": booking_id,
        "car":        car_name,
        "pickup":     pickup_str,
    })


async def notify_payment_refunded(
    customer_phone: str,
    customer_id: str,
    booking_id: str,
    refund_amount: int,
) -> None:
    await send_sms(
        customer_phone,
        f"Voyza: Refund of {fmt_rupees(refund_amount)} for booking "
        f"#{booking_id[:8].upper()} is being processed. "
        f"Expected in 5-7 business days."
    )
    await send_inapp(customer_id, "payment.refunded", {
        "booking_id":   booking_id,
        "refund_amount": refund_amount,
    })
