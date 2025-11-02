import os
from typing import List

DIR_PATH = os.getcwd()

# Local data storage
LOCAL_SAVE_PATH = "data/scrapped/"

# Model and Database Configuration
MODEL_PATH = DIR_PATH + "/" + "backend/model/0_CLIPModel/"
CHROMA_DB_PATH = DIR_PATH + "/" + "backend/data/chroma"
COLLECTION_NAME = DIR_PATH + "/" + "backend/vinted_dresses_db"

# Default catalog IDs for different categories
CATALOG_IDS = {
    "dresses": 10,
    "tops": 11,
    "skirts": 12,
    "pants": 13,
    "shoes": 14,
    "accessories": 15,
}

# Scraping Configuration
VINTED_BASE_URL = "https://www.vinted.fr"
VINTED_API_ENDPOINT = "/api/v2/catalog/items"

DEFAULT_CATALOG_ID = 10  # Dresses
MAX_PAGES_PER_SCRAPE = 20
ITEMS_PER_PAGE = 96
MAX_PAGES = 20
BATCH_SIZE = 6  # For embedding processing
MAX_RETRIES = 3
PAUSE_RANGE = (1.0, 2.5)  # Random pause between requests

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_WORKERS = 1

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(levelname)s] %(message)s"

# User Agents for scraping
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def get_config():
    """Return full configuration with environment variable overrides."""
    return {
        # Paths
        "dir_path": os.getenv("DIR_PATH", DIR_PATH),
        "local_save_path": os.getenv("LOCAL_SAVE_PATH", LOCAL_SAVE_PATH),
        "model_path": os.getenv("MODEL_PATH", MODEL_PATH),
        "chroma_db_path": os.getenv("CHROMA_DB_PATH", CHROMA_DB_PATH),
        "collection_name": os.getenv("COLLECTION_NAME", COLLECTION_NAME),
        # Catalog
        "catalog_ids": CATALOG_IDS,
        "default_catalog_id": int(os.getenv("DEFAULT_CATALOG_ID", DEFAULT_CATALOG_ID)),
        # Scraping
        "vinted_base_url": os.getenv("VINTED_BASE_URL", VINTED_BASE_URL),
        "vinted_api_endpoint": os.getenv("VINTED_API_ENDPOINT", VINTED_API_ENDPOINT),
        "max_pages": int(os.getenv("MAX_PAGES", MAX_PAGES)),
        "max_pages_per_scrape": int(
            os.getenv("MAX_PAGES_PER_SCRAPE", MAX_PAGES_PER_SCRAPE)
        ),
        "items_per_page": int(os.getenv("ITEMS_PER_PAGE", ITEMS_PER_PAGE)),
        "batch_size": int(os.getenv("BATCH_SIZE", BATCH_SIZE)),
        "max_retries": int(os.getenv("MAX_RETRIES", MAX_RETRIES)),
        "pause_range": (
            float(os.getenv("PAUSE_MIN", PAUSE_RANGE[0])),
            float(os.getenv("PAUSE_MAX", PAUSE_RANGE[1])),
        ),
        # API
        "api_host": os.getenv("API_HOST", API_HOST),
        "api_port": int(os.getenv("API_PORT", API_PORT)),
        "api_workers": int(os.getenv("API_WORKERS", API_WORKERS)),
        # Logging
        "log_level": os.getenv("LOG_LEVEL", LOG_LEVEL),
        "log_format": os.getenv("LOG_FORMAT", LOG_FORMAT),
        # User Agents
        "user_agents": os.getenv("USER_AGENTS", ",".join(USER_AGENTS)).split(","),
    }
