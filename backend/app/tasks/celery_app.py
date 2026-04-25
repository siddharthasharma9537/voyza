"""
app/tasks/celery_app.py
────────────────────────
Celery configuration and all async background tasks.

Tasks:
  send_booking_reminder     — dispatched at booking creation, fires 24h + 2h before pickup
  send_booking_confirmation — triggered after payment capture
  process_scheduled_refund  — runs after cancellation grace period
  cleanup_expired_otps      — scheduled every 30 min
  sync_platform_stats       — caches analytics to Redis every 5 min

Beat schedule (cron):
  Every 30 min: cleanup_expired_otps
  Every 5 min:  sync_platform_stats
  Every hour:   check_pickup_reminders
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# ── Celery app ────────────────────────────────────────────────────────────────
celery_app = Celery(
    "voyza",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # re-queue on worker crash
    worker_prefetch_multiplier=1,  # fair dispatch
    result_expires=3600,           # 1h result TTL
)

# ── Beat schedule ─────────────────────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "cleanup-expired-otps": {
        "task":     "app.tasks.jobs.maintenance.cleanup_expired_otps",
        "schedule": crontab(minute="*/30"),
    },
    "sync-platform-stats": {
        "task":     "app.tasks.jobs.maintenance.sync_platform_stats",
        "schedule": crontab(minute="*/5"),
    },
    "check-pickup-reminders": {
        "task":     "app.tasks.jobs.notifications.check_pickup_reminders",
        "schedule": crontab(minute=0),   # every hour
    },
}
