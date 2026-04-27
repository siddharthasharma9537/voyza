"""
app/services/email_service.py
─────────────────────────────
Email delivery service using SendGrid.
"""

import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings

logger = structlog.get_logger()


async def send_otp_email(email: str, otp: str, purpose: str = "verification") -> bool:
    """
    Send OTP via email using SendGrid.

    Args:
        email: Recipient email address
        otp: The OTP code to send
        purpose: Purpose of OTP (verification, password_reset, etc.)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured")
        return False

    try:
        # Create email subject and content based on purpose
        if purpose == "email_verification":
            subject = "Verify your Voyza email address"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #0284c7; margin-bottom: 20px;">Email Verification</h2>
                        <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                            Your Voyza verification code is:
                        </p>
                        <div style="background-color: #f0f4f8; border: 2px solid #0284c7; border-radius: 6px; padding: 20px; text-align: center; margin: 30px 0;">
                            <span style="font-size: 32px; font-weight: bold; color: #0284c7; letter-spacing: 4px;">{otp}</span>
                        </div>
                        <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                            This code expires in 10 minutes. Do not share this code with anyone.
                        </p>
                        <p style="color: #999; font-size: 12px;">
                            If you didn't request this code, please ignore this email.
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Voyza © 2024. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
        else:  # login or registration
            subject = "Your Voyza login code"
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #0284c7; margin-bottom: 20px;">Your Login Code</h2>
                        <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                            Your Voyza login code is:
                        </p>
                        <div style="background-color: #f0f4f8; border: 2px solid #0284c7; border-radius: 6px; padding: 20px; text-align: center; margin: 30px 0;">
                            <span style="font-size: 32px; font-weight: bold; color: #0284c7; letter-spacing: 4px;">{otp}</span>
                        </div>
                        <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                            This code expires in 10 minutes. Do not share this code with anyone.
                        </p>
                        <p style="color: #999; font-size: 12px;">
                            If you didn't request this code, please ignore this email.
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Voyza © 2024. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """

        # Create and send email
        message = Mail(
            from_email=(settings.EMAILS_FROM_EMAIL, settings.EMAILS_FROM_NAME),
            to_emails=email,
            subject=subject,
            html_content=html_body,
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info(
                "email_sent",
                email=email,
                purpose=purpose,
                status_code=response.status_code,
            )
            return True
        else:
            logger.warning(
                "email_send_failed",
                email=email,
                purpose=purpose,
                status_code=response.status_code,
            )
            return False

    except Exception as e:
        logger.error("email_send_error", email=email, purpose=purpose, exc_info=e)
        return False


async def send_welcome_email(email: str, full_name: str) -> bool:
    """Send welcome email to new user."""
    if not settings.SENDGRID_API_KEY:
        return False

    try:
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #0284c7; margin-bottom: 10px;">Welcome to Voyza, {full_name}!</h2>
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Your account has been successfully created. You're all set to start renting or listing cars.
                    </p>
                    <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                        Get started with Voyza and enjoy a seamless car rental experience.
                    </p>
                    <a href="{settings.BACKEND_URL}" style="display: inline-block; background-color: #0284c7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Go to Dashboard
                    </a>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Voyza © 2024. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """

        message = Mail(
            from_email=(settings.EMAILS_FROM_EMAIL, settings.EMAILS_FROM_NAME),
            to_emails=email,
            subject="Welcome to Voyza!",
            html_content=html_body,
        )

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        return response.status_code in (200, 201, 202)

    except Exception as e:
        logger.error("welcome_email_error", email=email, exc_info=e)
        return False
