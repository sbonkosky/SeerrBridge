"""
SeerrBridge - FastAPI entrypoint.
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from loguru import logger
import uvicorn

from seerr import __version__
from seerr.background_tasks import (
    ensure_setup,
    get_job_state,
    start_scheduler,
    stop_scheduler,
    trigger_job_run,
)
from seerr.browser import driver, initialize_browser, shutdown_browser
from seerr.config import load_config
from seerr.models import WebhookPayload
from seerr.realdebrid import check_and_refresh_access_token
from seerr.utils import START_TIME


def _format_uptime() -> dict:
    uptime_seconds = int((datetime.now() - START_TIME).total_seconds())
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = ""
    if days:
        uptime_str += f"{days}d "
    if hours or days:
        uptime_str += f"{hours}h "
    if minutes or hours or days:
        uptime_str += f"{minutes}m "
    uptime_str += f"{seconds}s"
    return {"uptime_seconds": uptime_seconds, "uptime": uptime_str.strip()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup and teardown for the FastAPI app."""
    logger.info(f"Booting SeerrBridge v{__version__}")
    if not load_config():
        logger.error("Configuration invalid; exiting.")
        os._exit(1)

    check_and_refresh_access_token()
    await initialize_browser()
    await ensure_setup()
    await start_scheduler()
    await trigger_job_run("startup")

    try:
        yield
    finally:
        await stop_scheduler()
        await shutdown_browser()


app = FastAPI(lifespan=lifespan)


@app.get("/status")
async def status():
    """Expose basic runtime information."""
    uptime_info = _format_uptime()
    job_state = get_job_state()
    return {
        "status": "running",
        "version": __version__,
        "browser_initialized": driver is not None,
        "job": job_state,
        **uptime_info,
    }


@app.post("/jellyseer-webhook/")
async def jellyseer_webhook(request: Request):
    """Trigger the job whenever Overseerr/Jellyseerr fires a webhook."""
    payload_data = await request.json()

    try:
        payload = WebhookPayload(**payload_data)
    except Exception as exc:
        logger.error(f"Invalid webhook payload: {exc}")
        raise HTTPException(status_code=400, detail="Invalid payload") from exc

    logger.info(f"Webhook received: event={payload.event}, notification={payload.notification_type}")

    if payload.notification_type == "TEST_NOTIFICATION":
        return {"status": "success", "message": "Test notification processed."}

    asyncio.create_task(trigger_job_run("webhook"))
    return {"status": "accepted"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8777)
