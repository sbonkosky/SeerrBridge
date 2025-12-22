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
    click_first_instant_rd_in_result_cards,
    ensure_with_extras_filter,
    has_rd_100_result,
    set_search_query,
)

SEARCH_PATTERNS = [
    # [
    #     r"^(?=.*(Remux|BluRay|BDRip|BDRemux|BRRip|WEB-DL))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    #     r"^(?=.*(Remux|BluRay|BDRip|BDRemux|BRRip|WEB-DL|WEBRip))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    # ],
    [
        r"^(?=.*(1080))(?=.*(Remux|BluRay|BDRip|BDRemux|BRRip|WEB-DL))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
        r"^(?=.*(1080))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    ],
    [
        r"^(?=.*(720))(?=.*(Remux|BluRay|BDRip|BDRemux|BRRip|WEB-DL))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
        r"^(?=.*(720))(?!.*【.*?】)(?!.*[\u0400-\u04FF])(?!.*\[esp\])(?!.*2xrus).*",
    ],
    [
        r"^(?!.*[\u0400-\u04FF])",
    ],
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
    complete, method = _show_search_loop(active_driver)
    if complete:
        suffix = f" via {method}" if method else ""
        logger.success(f"Season {season} for '{item.title}' complete{suffix}.")
        return True

    logger.warning(f"Season {season} for '{item.title}' incomplete.")
    return False


def _prepare_results_area(active_driver):
    """Allow the UI to load and expand the grid."""
    time.sleep(10)
    click_show_more_results(active_driver, attempts=3, wait_between=5)
    time.sleep(5)


def _movie_search_loop(active_driver):
    return _run_search_tiers(active_driver, whole_season=False)


def _show_search_loop(active_driver):
    found_any, clicked_any = _run_search_tiers(active_driver, whole_season=True)
    if found_any:
        method = "Instant RD (Whole Season)" if clicked_any else ""
        return True, method

    # Backup: enable "With extras" filter and click the first Instant RD in result cards.
    if _run_with_extras_instant_rd_tiers(active_driver):
        return True, "Instant RD (With extras)"

    return False, ""


def _run_with_extras_instant_rd_tiers(active_driver) -> bool:
    """Retry the same search tiers, but use the 'With extras' filter + card Instant RD click."""
    total_tiers = len(SEARCH_PATTERNS)
    for tier_index, tier_patterns in enumerate(SEARCH_PATTERNS, start=1):
        logger.debug(f"Starting WITH-EXTRAS search tier {tier_index}/{total_tiers} ({len(tier_patterns)} patterns).")
        for pattern in tier_patterns:
            logger.debug(f"WITH-EXTRAS searching grid with pattern: {pattern}")
            try:
                set_search_query(active_driver, pattern)
            except Exception as exc:
                logger.error(f"Failed to type search pattern '{pattern}': {exc}")
                continue

            # Enable the filter chip once results are present.
            ensure_with_extras_filter(active_driver)
            time.sleep(1)

            if click_first_instant_rd_in_result_cards(active_driver):
                time.sleep(5)
                return True

        logger.debug(f"WITH-EXTRAS search tier {tier_index} completed without Instant RD clicks.")
    return False


def _run_search_tiers(active_driver, *, whole_season: bool):
    """
    Iterate through quality tiers. The first three tiers always run to try gathering
    multiple versions. The final fallback tier only runs if none of the earlier tiers
    found a 100% RD match.
    """
    clicked_any = False
    found_any = False
    total_tiers = len(SEARCH_PATTERNS)

    for tier_index, tier_patterns in enumerate(SEARCH_PATTERNS, start=1):
        is_fallback_tier = tier_index == total_tiers
        if is_fallback_tier and found_any:
            logger.debug("Skipping fallback tier because earlier tiers succeeded.")
            continue

        logger.debug(f"Starting search tier {tier_index}/{total_tiers} ({len(tier_patterns)} patterns).")
        for pattern in tier_patterns:
            logger.debug(f"Searching grid with pattern: {pattern}")
            try:
                set_search_query(active_driver, pattern)
            except Exception as exc:
                logger.error(f"Failed to type search pattern '{pattern}': {exc}")
                continue

            if has_rd_100_result(active_driver):
                found_any = True
                logger.debug(f"Tier {tier_index} produced an RD 100 result without Instant RD click.")
                break  # move to next tier

            if click_instant_rd_button(active_driver, whole_season=whole_season):
                clicked_any = True
                time.sleep(5)
                if has_rd_100_result(active_driver):
                    found_any = True
                    logger.debug(f"Tier {tier_index} produced an RD 100 result after Instant RD click.")
                    break
        else:
            # Finished this tier without success
            logger.debug(f"Search tier {tier_index} completed without RD 100 results.")
            continue

    return found_any, clicked_any
