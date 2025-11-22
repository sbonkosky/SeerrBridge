"""
Search orchestration for Debrid Media Manager.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from loguru import logger
from selenium.common.exceptions import WebDriverException

from seerr import browser as browser_module
from seerr.browser import (
    click_instant_rd_button,
    click_show_more_results,
    has_rd_100_result,
    set_search_query,
)

SEARCH_PATTERNS = [
    r"^(?=.*(1080))(?=.*(Remux|BluRay|BDRip|BDRemux|BRRip|WEB-DL))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    r"^(?=.*(1080))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    r"^(?=.*(Remux|BluRay|BDRip|BRRip|WEB-DL))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    r"^(?=.*(Remux|BluRay|BDRip|BRRip|WEB-DL|WEBRip))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    r"^(?!.*[\u0400-\u04FF])",
]


@dataclass
class MediaWorkItem:
    """Unit of work pulled from Overseerr."""

    request_id: int
    tmdb_id: int
    title: str
    imdb_id: str
    media_type: str
    seasons: List[int] = field(default_factory=list)

    @property
    def is_show(self) -> bool:
        return self.media_type == "tv"


def run_media_job(work_items: List[MediaWorkItem]):
    """Process requests, prioritising movies before shows."""
    active_driver = browser_module.driver
    if not active_driver:
        logger.error("Browser driver is not ready; skipping job.")
        return

    movies = [item for item in work_items if not item.is_show]
    shows = [item for item in work_items if item.is_show]

    for item in movies:
        _process_movie(item, active_driver)

    for item in shows:
        _process_show(item, active_driver)


def _process_movie(item: MediaWorkItem, active_driver):
    """Drive the movie workflow."""
    url = f"https://debridmediamanager.com/movie/{item.imdb_id}"
    try:
        active_driver.get(url)
        logger.info(f"Processing movie '{item.title}' (request {item.request_id}, TMDB {item.tmdb_id})")
        _prepare_results_area(active_driver)
        hundred_found, clicked_instant = _movie_search_loop(active_driver)
        if hundred_found:
            logger.success(f"Movie '{item.title}' complete{' after Instant RD' if clicked_instant else ''}.")
        else:
            logger.warning(f"Movie '{item.title}' incomplete - no RD (100%) result found.")
    except WebDriverException as exc:
        logger.error(f"Selenium error while processing movie '{item.title}': {exc}")


def _process_show(item: MediaWorkItem, active_driver):
    """Process pending seasons for a TV show."""
    if not item.seasons:
        logger.info(f"No pending seasons for '{item.title}'; skipping.")
        return

    season_list = ", ".join(str(s) for s in item.seasons)
    logger.info(f"Processing show '{item.title}' (request {item.request_id}) for seasons {season_list}")

    completed = 0
    for season in item.seasons:
        try:
            if _process_show_season(item, season, active_driver):
                completed += 1
        except WebDriverException as exc:
            logger.error(f"Selenium error while processing {item.title} season {season}: {exc}")

    if completed == len(item.seasons):
        logger.success(f"Show '{item.title}' complete ({completed}/{len(item.seasons)} seasons).")
    else:
        logger.warning(f"Show '{item.title}' incomplete ({completed}/{len(item.seasons)} seasons).")


def _process_show_season(item: MediaWorkItem, season: int, active_driver) -> bool:
    """Run the season-specific logic."""
    url = f"https://debridmediamanager.com/show/{item.imdb_id}/{season}"
    active_driver.get(url)
    logger.info(f"Opened {item.title} season {season} page ({url}).")

    _prepare_results_area(active_driver)
    hundred_found, clicked = _show_search_loop(active_driver)
    if hundred_found:
        detail = " via Instant RD (Whole Season)" if clicked else ""
        logger.success(f"Season {season} for '{item.title}' complete{detail}.")
        return True

    logger.warning(f"Season {season} for '{item.title}' incomplete.")
    return False


def _prepare_results_area(active_driver):
    """Allow the UI to load and expand the grid."""
    time.sleep(10)
    click_show_more_results(active_driver, attempts=3, wait_between=5)
    time.sleep(5)


def _movie_search_loop(active_driver):
    hundred_found = False
    clicked = False
    for search in SEARCH_PATTERNS:
        logger.debug(f"Searching movie grid with pattern: {search}")
        try:
            set_search_query(active_driver, search)
        except Exception as exc:  # pragma: no cover - Selenium interaction
            logger.error(f"Failed to type search pattern '{search}': {exc}")
            continue

        if has_rd_100_result(active_driver):
            hundred_found = True
            break

        if click_instant_rd_button(active_driver):
            clicked = True
            time.sleep(5)
            if has_rd_100_result(active_driver):
                hundred_found = True
                break

    return hundred_found, clicked


def _show_search_loop(active_driver):
    hundred_found = False
    clicked = False
    for search in SEARCH_PATTERNS:
        logger.debug(f"Searching show grid with pattern: {search}")
        try:
            set_search_query(active_driver, search)
        except Exception as exc:  # pragma: no cover - Selenium interaction
            logger.error(f"Failed to type search pattern '{search}': {exc}")
            continue

        if has_rd_100_result(active_driver):
            hundred_found = True
            break

        if click_instant_rd_button(active_driver, whole_season=True):
            clicked = True
            time.sleep(5)
            if has_rd_100_result(active_driver):
                hundred_found = True
                break

    return hundred_found, clicked
