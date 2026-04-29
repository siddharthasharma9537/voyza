"""
app/services/sms_service.py
──────────────────────────
SMS delivery service using Twilio.
"""

import structlog
from twilio.rest import Client

from app.core.config import settings

logger = structlog.get_logger()


async def send_otp_sms(phone: str, otp: str, purpose: str = "verification") -> bool:
    """
    Send OTP via SMS using Twilio.

    Args:
        phone: Recipient phone number (in E.164 format: +91XXXXXXXXXX)
        otp: The OTP code to send
        purpose: Purpose of OTP (registration, login, email_verification, oauth_phone_linking)

    Returns:
        True if SMS sent successfully, False otherwise
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_FROM_NUMBER:
        logger.warning("Twilio credentials not configured")
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Create message based on purpose
        if purpose == "registration":
            message_body = f"Your Voyza registration code is: {otp}. Valid for 10 minutes. Do not share."
        elif purpose == "login":
            message_body = f"Your Voyza login code is: {otp}. Valid for 10 minutes. Do not share."
        elif purpose == "email_verification":
            message_body = f"Your Voyza email verification code is: {otp}. Valid for 10 minutes. Do not share."
        elif purpose == "oauth_phone_linking":
            message_body = f"Your Voyza phone verification code is: {otp}. Valid for 10 minutes. Do not share."
        else:
            message_body = f"Your Voyza code is: {otp}. Valid for 10 minutes. Do not share."

        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone,
        )

        logger.info(
            "sms_sent",
            phone=phone,
            purpose=purpose,
            message_sid=message.sid,
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
