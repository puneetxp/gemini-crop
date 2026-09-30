"""
Quota Reset Scheduled Job

Resets AI usage quota for all users at midnight IST daily.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import get_async_db_context
from app.services.ai_quota_service import AIQuotaService

logger = logging.getLogger(__name__)


async def reset_daily_quota_job():
    """
    Job function to reset daily quota for all users

    Called at midnight IST every day by APScheduler.
    """
    logger.info("Starting daily quota reset job")

    try:
        # Get database session
        async with get_async_db_context() as db:
            service = AIQuotaService(db)
            result = await service.reset_daily_quota()

            logger.info(
                f"Daily quota reset completed: {result.users_reset} users reset at {result.reset_time}"
            )
    except Exception as e:
        logger.error(f"Error in daily quota reset job: {e}", exc_info=True)


def setup_quota_reset_scheduler() -> AsyncIOScheduler:
    """
    Set up APScheduler for daily quota reset

    Returns:
        Configured AsyncIOScheduler instance
    """
    scheduler = AsyncIOScheduler()

    # Schedule job for midnight IST (00:00 Asia/Kolkata)
    scheduler.add_job(
        reset_daily_quota_job,
        trigger=CronTrigger(hour=0, minute=0, timezone="Asia/Kolkata"),
        id="daily_quota_reset",
        name="Reset AI usage quota at midnight IST",
        replace_existing=True,
    )

    logger.info("Quota reset scheduler configured for midnight IST")

    return scheduler


def start_quota_reset_scheduler():
    """
    Start the quota reset scheduler

    Call this function during application startup.
    """
    scheduler = setup_quota_reset_scheduler()
    scheduler.start()
    logger.info("Quota reset scheduler started")
    return scheduler


def stop_quota_reset_scheduler(scheduler: AsyncIOScheduler):
    """
    Stop the quota reset scheduler

    Call this function during application shutdown.

    Args:
        scheduler: AsyncIOScheduler instance to stop
    """
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Quota reset scheduler stopped")
