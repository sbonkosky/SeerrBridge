"""
Browser automation utilities for SeerrBridge.
"""
from __future__ import annotations

import io
import os
import platform
import time
import zipfile
from typing import Optional
from datetime import datetime

import requests
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from seerr.config import (
    HEADLESS_MODE,
    RD_ACCESS_TOKEN,
    RD_CLIENT_ID,
    RD_CLIENT_SECRET,
    RD_REFRESH_TOKEN,
)

driver: Optional[webdriver.Chrome] = None


def _prune_screenshots(screenshots_dir: str, *, max_keep: int) -> None:
    if max_keep <= 0:
        return

    try:
        entries = []
        for name in os.listdir(screenshots_dir):
            if not name.lower().endswith(".png"):
                continue
            path = os.path.join(screenshots_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                entries.append((os.path.getmtime(path), path))
            except OSError:
                continue

        # Keep space for the new screenshot we're about to write.
        target_keep = max(max_keep - 1, 0)
        if len(entries) <= target_keep:
            return

        entries.sort(key=lambda item: item[0])  # oldest first
        to_delete = entries[: max(0, len(entries) - target_keep)]
        for _, path in to_delete:
            try:
                os.remove(path)
            except OSError:
                continue
    except OSError:
        return


def save_debug_screenshot(name: str = "fullpage"):
    """
    Try to capture (almost) the full page in one screenshot by resizing
    the window height to match the document height.

    Returns: full path to the screenshot, or None on failure.
    """
    if os.getenv("SCREENSHOTS_ENABLED", "true").lower() != "true":
        return None

    global driver
    if driver is None:
        logger.warning("Cannot take full-page screenshot: driver is not initialized.")
        return None

    # Where to save
    screenshots_dir = os.getenv("SCREENSHOTS_DIR") or os.path.join("logs", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    try:
        max_keep = int(os.getenv("SCREENSHOTS_MAX_KEEP", "10"))
    except ValueError:
        max_keep = 10
    _prune_screenshots(screenshots_dir, max_keep=max_keep)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in name.strip().lower())[:80] or "screenshot"
    filename = f"{safe_name}_{timestamp}.png"
    path = os.path.join(screenshots_dir, filename)

    try:
        # Get page dimensions
        total_height = driver.execute_script("""
            return Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight,
                document.body.clientHeight,
                document.documentElement.clientHeight
            );
        """)
        viewport_width = driver.execute_script("return document.documentElement.clientWidth;")

        # Resize the window to fit the full height
        logger.info(f"Resizing window to {viewport_width}x{total_height} for full-page screenshot.")
        driver.set_window_size(viewport_width, total_height)
        time.sleep(1)  # let layout settle

        driver.save_screenshot(path)
        logger.info(f"Saved FULL-PAGE debug screenshot to {path}")
        return path
    except Exception as e:
        logger.error(f"Failed to save full-page screenshot: {e}")
        return None


def _build_chrome_options() -> ChromeOptions:
    """Create a Chrome options instance configured for headless automation."""
    options = webdriver.ChromeOptions()
    if HEADLESS_MODE:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--enable-logging")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    if (
        platform.system().lower() == "linux"
        and os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
    ):
        # Prefer an explicit container-provided Chrome path if available.
        chrome_bin = os.getenv("CHROME_BIN")
        if chrome_bin and os.path.exists(chrome_bin):
            options.binary_location = chrome_bin
        else:
            default_bin = "/usr/bin/google-chrome"
            if os.path.exists(default_bin):
                options.binary_location = default_bin
            else:
                logger.debug("RUNNING_IN_DOCKER set but no Chrome binary found at CHROME_BIN or /usr/bin/google-chrome.")
    return options


def _latest_chromedriver_path() -> Optional[str]:
    """
    Download the latest Chrome driver from Google's Chrome for Testing initiative.
    Returns the path if successful, otherwise None.
    """
    try:
        system = platform.system().lower()
        arch = platform.machine().lower()
        platform_map = {
            "windows": "win32" if platform.architecture()[0] == "32bit" else "win64",
            "linux": "linux64" if arch in {"x86_64"} else "linux-arm64",
            "darwin": "mac-arm64" if arch in {"arm64", "aarch64"} else "mac-x64",
        }
        platform_id = platform_map.get(system)
        if not platform_id:
            logger.warning("Unsupported OS for Chrome for Testing driver download.")
            return None

        response = requests.get(
            "https://googlechromelabs.github.io/chrome-for-testing/"
            "last-known-good-versions-with-downloads.json",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        downloads = data["channels"]["Stable"]["downloads"]["chromedriver"]
        download_url = next(
            (item["url"] for item in downloads if item["platform"] == platform_id),
            None,
        )
        if not download_url:
            logger.warning("Could not locate Chrome driver download URL.")
            return None

        driver_dir = os.path.join(os.path.dirname(__file__), "chromedriver")
        os.makedirs(driver_dir, exist_ok=True)

        logger.info(f"Downloading Chrome driver for {platform_id}")
        driver_zip = requests.get(download_url, timeout=20)
        driver_zip.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(driver_zip.content)) as archive:
            archive.extractall(driver_dir)

        executable = "chromedriver.exe" if system == "windows" else "chromedriver"
        driver_path = os.path.join(driver_dir, f"chromedriver-{platform_id}", executable)
        if system != "windows":
            os.chmod(driver_path, 0o755)

        return driver_path
    except Exception as exc:
        logger.warning(f"Failed to download Chrome driver: {exc}")
        return None


async def initialize_browser():
    """Start the Selenium browser session if it is not already running."""
    global driver
    if driver:
        return driver

    options = _build_chrome_options()
    env_driver_path = os.getenv("CHROME_DRIVER_PATH")

    try:
        if env_driver_path and os.path.exists(env_driver_path):
            service = Service(env_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            try:
                # Let Selenium Manager locate/download a matching driver for the installed browser.
                driver = webdriver.Chrome(options=options)
            except WebDriverException:
                chromedriver_path = _latest_chromedriver_path()
                if chromedriver_path and os.path.exists(chromedriver_path):
                    service = Service(chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    logger.info("Falling back to webdriver_manager for Chrome driver installation.")
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        driver.get("https://debridmediamanager.com")
        _inject_real_debrid_tokens()
        login(driver)
        logger.success("Browser session initialized.")
        return driver
    except WebDriverException as exc:
        logger.error(f"Failed to initialize browser: {exc}")
        driver = None
        raise


async def shutdown_browser():
    """Close Selenium and clean up resources."""
    global driver
    if driver:
        driver.quit()
        driver = None
        logger.info("Browser session terminated.")


def _inject_real_debrid_tokens():
    """Insert Real-Debrid credentials into local storage for the current session."""
    if not driver:
        return
    driver.execute_script(
        """
        localStorage.setItem('rd:accessToken', arguments[0]);
        localStorage.setItem('rd:clientId', arguments[1]);
        localStorage.setItem('rd:clientSecret', arguments[2]);
        localStorage.setItem('rd:refreshToken', arguments[3]);
        """,
        RD_ACCESS_TOKEN,
        f'"{RD_CLIENT_ID}"',
        f'"{RD_CLIENT_SECRET}"',
        f'"{RD_REFRESH_TOKEN}"',
    )
    driver.refresh()


def login(active_driver):
    """Click the Real-Debrid login button when present."""
    try:
        button = WebDriverWait(active_driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login with Real Debrid')]"))
        )
        button.click()
        logger.info("Clicked 'Login with Real Debrid'.")
    except TimeoutException:
        logger.debug("Login button not visible; assuming session already authenticated.")


def apply_size_limits(max_movie_size: str, max_episode_size: str):
    """
    Apply the configured movie and episode size limits on the settings page.
    Raises RuntimeError if the browser session is unavailable.
    """
    if not driver:
        raise RuntimeError("Browser driver is not initialized.")

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            driver.get("https://debridmediamanager.com/settings")
            wait = WebDriverWait(driver, 20)

            # If the session needs re-auth, try clicking the login button.
            try:
                login_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login with Real Debrid')]"))
                )
                login_button.click()
                logger.info("Clicked 'Login with Real Debrid' from settings page.")
            except TimeoutException:
                pass

            movie_select = wait.until(EC.element_to_be_clickable((By.ID, "dmm-movie-max-size")))
            episode_select = wait.until(EC.element_to_be_clickable((By.ID, "dmm-episode-max-size")))

            Select(movie_select).select_by_value(str(max_movie_size))
            Select(episode_select).select_by_value(str(max_episode_size))
            logger.success(f"Applied movie size {max_movie_size} GB and episode size {max_episode_size} GB.")
            save_debug_screenshot("dmm-settings-applied")
            return
        except (TimeoutException, WebDriverException) as exc:
            last_exc = exc
            logger.warning(f"Failed to apply size limits (attempt {attempt}/3): {exc!r}")
            save_debug_screenshot(f"dmm-settings-failed-{attempt}")
            time.sleep(2)

    raise RuntimeError("Failed to apply size limits after retries.") from last_exc


def click_show_more_results(active_driver, attempts: int = 3, wait_between: int = 5):
    """Click the 'Show More Results' button multiple times when it is available."""
    for attempt in range(attempts):
        try:
            button = WebDriverWait(active_driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Show More Results')]")
                )
            )
            button.click()
            logger.debug(f"Clicked 'Show More Results' ({attempt + 1}/{attempts}).")
            time.sleep(wait_between)
        except TimeoutException:
            logger.debug(f"No 'Show More Results' button found on attempt {attempt + 1}.")
            break
        except ElementClickInterceptedException as exc:
            logger.warning(f"Failed to click 'Show More Results': {exc}")
            break


def _focus_search_input(active_driver):
    return WebDriverWait(active_driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#query")))


def set_search_query(active_driver, text: str, wait_after: float = 2.0):
    """Clear the search bar and type the provided text."""
    try:
        input_box = _focus_search_input(active_driver)
        input_box.click()
        input_box.send_keys(Keys.CONTROL, "a")
        input_box.send_keys(Keys.DELETE)
        input_box.send_keys(text)
        input_box.send_keys(Keys.ENTER)
        time.sleep(wait_after)
    except Exception as exc:
        save_debug_screenshot(f"set-search-query-failed")
        logger.error(f"Failed to type search query '{text}': {exc}")
        raise


def has_rd_100_result(active_driver, timeout: float = 2.0) -> bool:
    """
    Return True if there is an 'RD (100%)' match that is not a "Single" result card.

    Valid cards are those labelled as "Complete ..." or "With extras ...".
    """
    try:
        grid_xpath = (
            "//div[contains(@class,'grid-cols-1') and contains(@class,'gap-2') and contains(@class,'overflow-x-auto')]"
        )
        grid = WebDriverWait(active_driver, timeout).until(EC.presence_of_element_located((By.XPATH, grid_xpath)))

        rd_elements = grid.find_elements(By.XPATH, ".//*[contains(normalize-space(), 'RD (100%)')]")
        if not rd_elements:
            return False

        card_xpath = "ancestor::div[contains(@class,'overflow-hidden') and contains(@class,'rounded-lg')][1]"
        status_xpath = (
            ".//span[starts-with(normalize-space(),'Single') "
            "or starts-with(normalize-space(),'Complete') "
            "or starts-with(normalize-space(),'With extras') "
            "or starts-with(normalize-space(),'With Extras')]"
        )

        for rd_el in rd_elements:
            try:
                card = rd_el.find_element(By.XPATH, card_xpath)
            except NoSuchElementException:
                continue

            status_texts = []
            for el in card.find_elements(By.XPATH, status_xpath):
                text = (el.text or "").strip()
                if text:
                    status_texts.append(text)

            if any(text.startswith("Single") for text in status_texts):
                logger.debug("Found an 'RD (100%)' match on a Single card; ignoring.")
                save_debug_screenshot("found-rd-100-single-ignored")
                continue

            if any(text.startswith("Complete") for text in status_texts) or any(
                text.lower().startswith("with extras") for text in status_texts
            ):
                logger.debug("Found a valid 'RD (100%)' result (Complete/With extras).")
                save_debug_screenshot("found-rd-100-valid")
                return True

            logger.debug("Found an 'RD (100%)' match but could not validate card status; ignoring.")
            save_debug_screenshot("found-rd-100-unvalidated-ignored")

        return False
    except TimeoutException:
        return False


def click_instant_rd_button(active_driver, *, whole_season: bool = False, timeout: float = 3.0) -> bool:
    """Click the top banner Instant RD buttons shown in the screenshots."""
    if whole_season:
        xpath = (
            "//button[contains(@class, 'mb-1') and contains(normalize-space(), 'Instant RD') "
            "and contains(normalize-space(), 'Whole Season')]"
        )
        label = "Instant RD (Whole Season)"
    else:
        xpath = (
            "//button[contains(@class, 'mb-1') and contains(normalize-space(), 'Instant RD') "
            "and not(contains(normalize-space(), 'Whole Season'))]"
        )
        label = "Instant RD"
    safe_label = "".join(ch if ch.isalnum() else "-" for ch in label.lower())

    try:
        button = WebDriverWait(active_driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        button.click()
        logger.info(f"Clicked '{label}' button.")
        return True
    except TimeoutException:
        logger.debug(f"No '{label}' button available.")
        save_debug_screenshot(f"missing-{safe_label}")
        return False
    except ElementClickInterceptedException as exc:
        logger.warning(f"Unable to click '{label}': {exc}")
        return False


def ensure_with_extras_filter(active_driver, timeout: float = 5.0) -> bool:
    """
    Ensure the "With extras" filter chip is enabled.
    Returns True if the chip is present (enabled or successfully clicked), else False.
    """
    xpath = "//span[normalize-space()='With extras' or normalize-space()='With Extras']"
    try:
        chip = WebDriverWait(active_driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        logger.debug("No 'With extras' filter chip found.")
        return False

    cls = (chip.get_attribute("class") or "").lower()
    if "bg-blue-900" in cls:
        return True

    try:
        chip = WebDriverWait(active_driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        chip.click()
        time.sleep(1)
        return True
    except Exception as exc:
        logger.warning(f"Failed to enable 'With extras' filter chip: {exc!r}")
        save_debug_screenshot("with-extras-click-failed")
        return False


def click_first_instant_rd_in_result_cards(active_driver, timeout: float = 5.0) -> bool:
    """
    Click the first "Instant RD" button inside the result card grid.
    This intentionally does not use the top banner buttons.
    """
    grid_xpath = (
        "//div[contains(@class,'grid-cols-1') and contains(@class,'gap-2') and contains(@class,'overflow-x-auto')]"
    )
    try:
        grid = WebDriverWait(active_driver, timeout).until(EC.presence_of_element_located((By.XPATH, grid_xpath)))
        buttons = grid.find_elements(By.XPATH, ".//button[.//b[normalize-space()='Instant RD']]")
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                active_driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                WebDriverWait(active_driver, timeout).until(lambda d: button.is_enabled())
                button.click()
                logger.info("Clicked 'Instant RD' from result card grid.")
                return True
            except Exception:
                continue

        logger.debug("No 'Instant RD' buttons found inside result card grid.")
        save_debug_screenshot("no-instant-rd-in-cards")
        return False
    except TimeoutException:
        logger.debug("Result card grid not found.")
        save_debug_screenshot("missing-result-grid")
        return False
