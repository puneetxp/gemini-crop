"""SLUSI Ingestion Scheduled Job — runs every N days (configurable)."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)


async def run_slusi_ingestion_job() -> None:
    """Scheduled job: run SLUSI DSS + microwatershed ingestion."""
    logger.info("Starting scheduled SLUSI ingestion job")
    try:
        from fastapi import HTTPException

        from app.core.database import get_db_context
        from app.services.slusi_service import SLUSIService

        with get_db_context() as db:
            service = SLUSIService(db)
            try:
                result = await service.run_ingestion()
                logger.info(
                    "SLUSI ingestion completed: status=%s lcc=%d maps=%d",
                    result.status,
                    result.lcc_records_ingested,
                    result.maps_ingested,
                )
            except HTTPException as e:
                if e.status_code == 409:
                    logger.info("SLUSI ingestion skipped — run already in progress")
                else:
                    raise
    except Exception as exc:
        logger.error("SLUSI ingestion job failed: %s", exc, exc_info=True)


def start_slusi_scheduler() -> AsyncIOScheduler:
    """Start the SLUSI ingestion scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_slusi_ingestion_job,
        trigger=IntervalTrigger(days=settings.SLUSI_INGEST_INTERVAL_DAYS),
        id="slusi_ingestion",
        name=f"SLUSI ingestion every {settings.SLUSI_INGEST_INTERVAL_DAYS} days",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "SLUSI ingestion scheduler started (interval: %d days)",
        settings.SLUSI_INGEST_INTERVAL_DAYS,
    )
    return scheduler


def stop_slusi_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Stop the SLUSI ingestion scheduler."""
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("SLUSI ingestion scheduler stopped")
