"""
Configuration module for SeerrBridge
Loads environment variables and provides configuration values
"""
import os
import sys
import json
import time
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from loguru import logger

# Configure loguru
logger.remove()  # Remove default handler
logger.add("logs/seerrbridge.log", rotation="500 MB", encoding='utf-8')  # Use utf-8 encoding for log file
logger.add(sys.stdout, colorize=True)  # Ensure stdout can handle Unicode
logger.level("WARNING", color="<cyan>")
logger.level("DEBUG", color="<yellow>")

# Initialize variables
RD_ACCESS_TOKEN = None
RD_REFRESH_TOKEN = None
RD_CLIENT_ID = None
RD_CLIENT_SECRET = None
OVERSEERR_BASE = None
OVERSEERR_API_BASE_URL = None
OVERSEERR_API_KEY = None
TRAKT_API_KEY = None
HEADLESS_MODE = True
MAX_MOVIE_SIZE = None
MAX_EPISODE_SIZE = None
JOB_INTERVAL_SECONDS = 180

# Add a global variable to track start time
START_TIME = datetime.now()

def load_config(override: bool = False):
    """Load configuration from environment variables"""
    global RD_ACCESS_TOKEN, RD_REFRESH_TOKEN, RD_CLIENT_ID, RD_CLIENT_SECRET
    global OVERSEERR_BASE, OVERSEERR_API_BASE_URL, OVERSEERR_API_KEY, TRAKT_API_KEY
    global HEADLESS_MODE, MAX_MOVIE_SIZE, MAX_EPISODE_SIZE, JOB_INTERVAL_SECONDS
    
    # Load environment variables
    load_dotenv(override=override)
    
    # Securely load credentials from environment variables
    RD_ACCESS_TOKEN = os.getenv('RD_ACCESS_TOKEN')
    RD_REFRESH_TOKEN = os.getenv('RD_REFRESH_TOKEN')
    RD_CLIENT_ID = os.getenv('RD_CLIENT_ID')
    RD_CLIENT_SECRET = os.getenv('RD_CLIENT_SECRET')
    OVERSEERR_BASE = os.getenv('OVERSEERR_BASE')
    OVERSEERR_API_BASE_URL = f"{OVERSEERR_BASE}/api/v1" if OVERSEERR_BASE else None
    OVERSEERR_API_KEY = os.getenv('OVERSEERR_API_KEY')
    TRAKT_API_KEY = os.getenv('TRAKT_API_KEY')
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    MAX_MOVIE_SIZE = os.getenv("MAX_MOVIE_SIZE")
    MAX_EPISODE_SIZE = os.getenv("MAX_EPISODE_SIZE")

    try:
        JOB_INTERVAL_SECONDS = int(os.getenv("JOB_INTERVAL_SECONDS", "180"))
        if JOB_INTERVAL_SECONDS < 60:
            logger.warning("JOB_INTERVAL_SECONDS too low; using minimum of 60 seconds.")
            JOB_INTERVAL_SECONDS = 60
    except (TypeError, ValueError):
        logger.error("JOB_INTERVAL_SECONDS is not a valid integer. Falling back to 180 seconds.")
        JOB_INTERVAL_SECONDS = 180
    
    # Validate required configuration
    if not OVERSEERR_API_BASE_URL:
        logger.error("OVERSEERR_API_BASE_URL environment variable is not set.")
        return False
    
    if not OVERSEERR_API_KEY:
        logger.error("OVERSEERR_API_KEY environment variable is not set.")
        return False
    
    if not TRAKT_API_KEY:
        logger.error("TRAKT_API_KEY environment variable is not set.")
        return False
    
    return True

# Initialize configuration
load_config()

def update_env_file():
    """Update the .env file with the new access token."""
    try:
        with open('.env', 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        with open('.env', 'w', encoding='utf-8') as file:
            for line in lines:
                if line.startswith('RD_ACCESS_TOKEN'):
                    file.write(f'RD_ACCESS_TOKEN={RD_ACCESS_TOKEN}\n')
                else:
                    file.write(line)
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False 
