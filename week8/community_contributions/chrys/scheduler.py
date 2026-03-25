"""APScheduler: 30 min during market hours, 2 hr outside (24/7 assets only)."""
from datetime import datetime, timezone, timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from orchestrator import run_pipeline
from config import MARKET_OPEN_HOUR_ET, MARKET_CLOSE_HOUR_ET

logger = logging.getLogger("aria.scheduler")


def _is_market_hours() -> bool:
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now = datetime.now(timezone.utc) - timedelta(hours=5)
    if now.weekday() >= 5:
        return False
    return MARKET_OPEN_HOUR_ET <= now.hour < MARKET_CLOSE_HOUR_ET


def _job():
    try:
        run_pipeline()
    except Exception as e:
        logger.exception("Pipeline run failed: %s", e)


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Every 30 min when market open, every 2 hr otherwise
    scheduler.add_job(_job, IntervalTrigger(minutes=30), id="aria_pipeline")
    scheduler.start()
    logger.info("ARIA scheduler started (30 min interval; decision agent gates by market hours)")
    return scheduler
