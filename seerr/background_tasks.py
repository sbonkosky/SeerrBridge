"""
Periodic job orchestration for SeerrBridge.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from loguru import logger

from seerr import browser as browser_module
from seerr.config import JOB_INTERVAL_SECONDS, MAX_EPISODE_SIZE, MAX_MOVIE_SIZE
from seerr.overseerr import get_overseerr_media_requests
from seerr.search import MediaWorkItem, run_media_job
from seerr.trakt import get_media_details_from_trakt

AVAILABLE_STATUS_CODES = {4, 5}  # Overseerr status codes for PARTIALLY_AVAILABLE / AVAILABLE

_setup_complete = False
_job_lock = asyncio.Lock()
_scheduler_task: Optional[asyncio.Task] = None

_state = {
    "job_running": False,
    "last_trigger": None,
    "last_run_started": None,
    "last_run_completed": None,
    "last_error": None,
}


async def start_scheduler():
    """Kick off the periodic job loop."""
    global _scheduler_task
    if _scheduler_task is None:
        _scheduler_task = asyncio.create_task(_job_loop())
        logger.info(f"Background job scheduled every {JOB_INTERVAL_SECONDS} seconds.")


async def stop_scheduler():
    """Stop the scheduler task if it is running."""
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        logger.info("Background job scheduler stopped.")


def get_job_state():
    """Expose scheduler status for the status endpoint."""
    def _format(dt: Optional[datetime]):
        return dt.isoformat() if isinstance(dt, datetime) else None

    return {
        "setup_complete": _setup_complete,
        "job_running": _state["job_running"],
        "job_interval_seconds": JOB_INTERVAL_SECONDS,
        "last_trigger": _state["last_trigger"],
        "last_run_started": _format(_state["last_run_started"]),
        "last_run_completed": _format(_state["last_run_completed"]),
        "last_error": _state["last_error"],
    }


async def trigger_job_run(trigger_source: str):
    """Run the job immediately (used by the timer and webhook)."""
    if not await ensure_setup():
        logger.warning(f"Setup incomplete; skipping job run triggered by {trigger_source}.")
        return False

    if _job_lock.locked():
        logger.info(f"Job already running; {trigger_source} trigger ignored.")
        return False

    async with _job_lock:
        _state["job_running"] = True
        _state["last_trigger"] = trigger_source
        _state["last_run_started"] = datetime.utcnow()
        _state["last_error"] = None

        try:
            _run_once()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception(f"Job execution failed: {exc}")
            _state["last_error"] = str(exc)
        finally:
            _state["last_run_completed"] = datetime.utcnow()
            _state["job_running"] = False

    return True


async def ensure_setup() -> bool:
    """Ensure the browser is ready and the DMM settings are configured."""
    global _setup_complete

    if browser_module.driver is None:
        await browser_module.initialize_browser()

    if _setup_complete:
        return True

    if not MAX_MOVIE_SIZE or not MAX_EPISODE_SIZE:
        logger.error("MAX_MOVIE_SIZE and MAX_EPISODE_SIZE must be configured.")
        return False

    try:
        browser_module.apply_size_limits(MAX_MOVIE_SIZE, MAX_EPISODE_SIZE)
        _setup_complete = True
        logger.success("Initial Debrid Media Manager setup complete.")
    except Exception as exc:
        logger.error(f"Failed to apply size limits: {exc}")
        return False

    return True


def _run_once():
    """Fetch pending requests from Overseerr and dispatch the Selenium workflow."""
    # Re-apply size limits at the start of every job to ensure settings
    # stay in sync with the configured environment.
    try:
        browser_module.apply_size_limits(MAX_MOVIE_SIZE, MAX_EPISODE_SIZE)
        logger.debug("Re-applied Debrid Media Manager size limits at start of job.")
    except Exception as exc:
        logger.error(f"Failed to re-apply size limits at job start: {exc}")

    requests = get_overseerr_media_requests()
    if not requests:
        logger.info("No pending Overseerr requests.")
        return

    work_items = _build_work_items(requests)
    if not work_items:
        logger.info("All requests are already satisfied or invalid.")
        return

    movie_count = _count_movies(work_items)
    show_count = _count_shows(work_items)
    logger.info(f"Processing {movie_count} movie(s) and {show_count} show(s).")
    run_media_job(work_items)


def _build_work_items(requests: List[dict]) -> List[MediaWorkItem]:
    items: List[MediaWorkItem] = []
    for request in requests:
        media = request.get("media") or {}
        tmdb_id = media.get("tmdbId")
        media_type = media.get("mediaType")
        request_id = request.get("id")

        if not tmdb_id or not media_type:
            logger.debug(f"Skipping request without tmdbId or mediaType: {request}")
            continue

        details = get_media_details_from_trakt(str(tmdb_id), media_type)
        if not details or not details.get("imdb_id"):
            logger.warning(f"Unable to fetch details for TMDB ID {tmdb_id} ({media_type}).")
            continue

        title = details["title"]
        if details.get("year"):
            title = f"{title} ({details['year']})"

        seasons = []
        if media_type == "tv":
            seasons = _pending_seasons(request)
            if not seasons:
                logger.info(f"Skipping show '{title}' - no pending seasons.")
                continue

        items.append(
            MediaWorkItem(
                request_id=request_id or 0,
                tmdb_id=tmdb_id,
                title=title,
                imdb_id=details["imdb_id"],
                media_type=media_type,
                seasons=seasons,
            )
        )
    return items


def _pending_seasons(request: dict) -> List[int]:
    pending = []
    for season in request.get("seasons", []):
        status = season.get("status")
        number = season.get("seasonNumber")
        if status in AVAILABLE_STATUS_CODES:
            continue
        if number is not None:
            pending.append(int(number))
    return pending


def _count_movies(items: List[MediaWorkItem]) -> int:
    return sum(1 for item in items if item.media_type == "movie")


def _count_shows(items: List[MediaWorkItem]) -> int:
    return sum(1 for item in items if item.media_type == "tv")


async def _job_loop():
    """Background loop that triggers the job based on the configured interval."""
    try:
        while True:
            await asyncio.sleep(JOB_INTERVAL_SECONDS)
            await trigger_job_run("timer")
    except asyncio.CancelledError:
        logger.debug("Job loop cancelled.")
