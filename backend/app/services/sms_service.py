"""
app/services/sms_service.py
────────────────────────────
SMS delivery service using Twilio.
"""

import structlog
from twilio.rest import Client

from app.core.config import settings

logger = structlog.get_logger()


async def send_otp_sms(phone: str, otp: str, purpose: str = "login") -> bool:
    """
    Send OTP via SMS using Twilio.

    Args:
        phone: Phone number in format: 9876543210 (or +919876543210)
        otp: The OTP code to send
        purpose: Purpose of OTP (login, registration, verification, etc.)

    Returns:
        True if SMS sent successfully, False otherwise
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured")
        return False

    try:
        # Format phone number: ensure it has country code
        if not phone.startswith("+"):
            phone = f"+91{phone}"  # Add India country code

        # Create Twilio client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Create message based on purpose
        if purpose == "registration":
            message_body = f"Your Voyza registration code is: {otp}\n\nValid for 10 minutes. Do not share."
        elif purpose == "email_verification":
            message_body = f"Your Voyza email verification code is: {otp}\n\nValid for 10 minutes. Do not share."
        else:  # login or other
            message_body = f"Your Voyza login code is: {otp}\n\nValid for 10 minutes. Do not share."

        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )

        logger.info(
            "sms_sent",
            phone=phone,
            purpose=purpose,
            message_id=message.sid,
        )
        return True

    except Exception as e:
        logger.error(
            "sms_send_error",
            phone=phone,
            purpose=purpose,
            exc_info=e,
        )
        return False


async def send_welcome_sms(phone: str, full_name: str) -> bool:
    """Send welcome SMS to new user."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return False

    try:
        if not phone.startswith("+"):
            phone = f"+91{phone}"

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message_body = f"Welcome to Voyza, {full_name}! 🚗\n\nYour account is ready. Start renting or listing cars now."

        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )

        logger.info("welcome_sms_sent", phone=phone, message_id=message.sid)
        return True

    except Exception as e:
        logger.error("welcome_sms_error", phone=phone, exc_info=e)
        return False
