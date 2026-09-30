"""
Weekly Yield Prediction Update Job
Background job to update yield predictions for all active crops

Task 25.3: Implement real-time yield prediction updates
Validates: Requirements AC10.4 (Phase 6 - Required)
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.yield_prediction_update_service import get_yield_prediction_update_service

logger = logging.getLogger(__name__)


async def run_weekly_yield_update():
    """
    Run weekly yield prediction update job

    This job should be scheduled to run weekly (e.g., every Sunday at 6 AM)
    using a task scheduler like:
    - AWS EventBridge (for production)
    - Celery Beat (for self-hosted)
    - APScheduler (for simple deployments)

    Validates: AC10.4 - Weekly yield prediction updates
    """
    logger.info("Starting weekly yield prediction update job")
    start_time = datetime.now()

    try:
        # Get database session
        async with get_async_session() as db:
            # Get service
            service = get_yield_prediction_update_service(db)

            # Run update job
            summary = await service.run_weekly_update_job()

            # Log results
            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Weekly yield update job completed in {duration:.2f}s: "
                f"Checked {summary.get('crops_checked', 0)} crops, "
                f"Updated {summary.get('predictions_updated', 0)} predictions, "
                f"Sent {summary.get('harvest_alerts_sent', 0)} alerts, "
                f"Errors: {summary.get('errors', 0)}"
            )

            return summary

    except Exception as e:
        logger.error(f"Error in weekly yield update job: {e}")
        raise


if __name__ == "__main__":
    """
    Run job manually for testing

    Usage:
        python -m app.jobs.weekly_yield_update
    """
    asyncio.run(run_weekly_yield_update())
