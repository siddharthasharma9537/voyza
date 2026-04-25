"""
app/tasks/jobs/maintenance.py
──────────────────────────────
Scheduled maintenance tasks.
"""

import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import delete, select

from app.db.base import AsyncSessionLocal
from app.models import OTPCode

logger = logging.getLogger(__name__)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@shared_task
def cleanup_expired_otps():
    """Delete OTP records older than 30 minutes. Runs every 30 min."""
    async def _inner():
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(OTPCode).where(OTPCode.expires_at < now)
            )
            await db.commit()
            deleted = result.rowcount
            logger.info("otp_cleanup", deleted=deleted)
            return deleted

    return _run(_inner())


@shared_task
def sync_platform_stats():
    """
    Compute platform analytics and cache to Redis.
    Runs every 5 min — prevents analytics endpoint from hitting DB on every request.
    """
    async def _inner():
        try:
            import redis.asyncio as aioredis
            import json
            from app.core.config import settings
            from app.services.admin_service import get_platform_analytics

            async with AsyncSessionLocal() as db:
                analytics = await get_platform_analytics(db)

            r = aioredis.from_url(settings.redis_url)
            await r.setex(
                "platform:analytics",
                300,   # 5 min TTL
                analytics.model_dump_json(),
            )
            await r.aclose()
            logger.info("platform_stats_synced")
        except Exception as e:
            logger.error("stats_sync_failed", error=str(e))

    _run(_inner())
