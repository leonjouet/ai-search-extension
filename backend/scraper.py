"""
Vinted Scraper
Extracts items from Vinted
"""

import os
import time
import random
import json
import re
import logging
import argparse
from typing import List, Dict, Any, Optional, Union
import requests
import pandas as pd
import cloudscraper
from typing import List, Union, Optional, Dict, Any, Iterable

from config import get_config

config = get_config()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class VintedScraper:
    """Main scraper class for Vinted items and embeddings"""

    def __init__(
        self,
        local_save_path: str = config["local_save_path"],
        api_link: str = config["vinted_api_endpoint"],
        vinted_link: str = config["vinted_base_url"],
        catalog_id: int = config["catalog_ids"]["dresses"],
        max_pages: int = config["max_pages"],
        per_page: int = config["max_pages_per_scrape"],
    ):
        self.local_save_path = local_save_path
        self.vinted_link = vinted_link
        self.api_link = api_link
        self.catalog_id = catalog_id
        self.max_pages = max_pages
        self.per_page = per_page

    def create_public_session_fr(self) -> requests.Session:
        """Create a public session for the Vinted website"""
        import browser_cookie3

        ua_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]

        csrf_regex = re.compile(r'"CSRF_TOKEN":"([^"]+)"')

        s = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True},
            delay=10,
        )
        s.headers.update(
            {
                "User-Agent": random.choice(ua_pool),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "Referer": self.vinted_link + "/",
                "Origin": self.vinted_link,
                "Connection": "keep-alive",
                "sec-ch-ua": '"Google Chrome";v="126", "Chromium";v="126", "Not=A?Brand";v="99"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
            }
        )

        try:
            cookies = browser_cookie3.chrome(domain_name="vinted.fr")
            for c in cookies:
                s.cookies.set(c.name, c.value)
            logger.info(f"Loaded {len(cookies)} cookies from Chrome for vinted.fr")
        except Exception as e:
            logger.warning(f"Could not load browser cookies: {e}")

        # Optional: short delay before first request
        time.sleep(random.uniform(2.5, 5.0))

        # Try initial request to establish session
        r = s.get(self.vinted_link, timeout=15)
        if r.status_code != 200:
            logger.warning(f"Initial Vinted page load failed with {r.status_code}")
        else:
            m = csrf_regex.search(r.text)
            if m:
                s.headers["X-CSRF-Token"] = m.group(1)

        return s

    def fetch_vinted_items_fr(
        self,
        search_text: Optional[str] = None,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        brand_ids: Optional[Union[int, List[int], str]] = None,
        size_ids: Optional[Union[int, List[int], str]] = None,
        color_ids: Optional[Union[int, List[int], str]] = None,
        pause_range: tuple = config["pause_range"],
        max_retries: int = config["max_retries"],
        save_json_path: Optional[str] = None,
        verbose: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch public item listings from Vinted France.

        Parameters:
            catalog_id: Single ID or list of category (catalog) IDs.
            search_text: Free text search (French site context).
            max_pages: Max pagination pages to retrieve.
            per_page: Items per request (<= 96 typical).
            price_from / price_to: Price bounds.
            brand_ids / size_ids / color_ids: Filter lists or comma strings.
            pause_range: (min,max) seconds random sleep between pages.
            max_retries: Retry attempts per page on transient errors.
            save_json_path: If provided, save final list as JSON.
            verbose: Log progress.

        Returns:
            List of raw item JSON dictionaries.
        """

        session = self.create_public_session_fr()

        def norm_list(val):
            if val is None:
                return None
            if isinstance(val, str):
                return val
            if isinstance(val, int):
                return str(val)
            return ",".join(str(x) for x in val)

        params_base = {
            "order": "newest_first",
            "page": 1,
            "per_page": self.per_page,
            "time": int(time.time()),  # sometimes included; harmless
        }
        if self.catalog_id is not None:
            params_base["catalog_id"] = norm_list(self.catalog_id)
        if search_text:
            params_base["search_text"] = search_text
        if price_from is not None:
            params_base["price_from"] = price_from
        if price_to is not None:
            params_base["price_to"] = price_to
        if brand_ids is not None:
            params_base["brand_ids"] = norm_list(brand_ids)
        if size_ids is not None:
            params_base["size_ids"] = norm_list(size_ids)
        if color_ids is not None:
            params_base["color_ids"] = norm_list(color_ids)

        collected: List[Dict[str, Any]] = []

        for page in range(1, self.max_pages + 1):
            params = dict(params_base)
            params["page"] = page

            attempt = 0
            while attempt < max_retries:
                attempt += 1
                try:
                    resp = session.get(self.api_link, params=params, timeout=15)
                    if resp.status_code == 403:
                        if verbose:
                            logging.warning(
                                f"403 Forbidden: refreshing session and retrying (attempt {attempt}/{max_retries})"
                            )
                        session = self.create_public_session_fr()
                        time.sleep(random.uniform(2, 5))
                        continue

                    if resp.status_code == 429:
                        wait_s = 5 + attempt * 3
                        if verbose:
                            logging.warning(
                                f"429 Too Many Requests. Backing off {wait_s}s (attempt {attempt}/{max_retries})"
                            )
                        time.sleep(wait_s)
                        continue

                    if resp.status_code == 401:
                        logging.error(
                            "401 Unauthorized. Public access blocked; consider adding authenticated cookies."
                        )
                        return collected
                    if resp.status_code >= 500:
                        if verbose:
                            logging.warning(
                                f"Server error {resp.status_code}. Retry {attempt}/{max_retries}"
                            )
                        time.sleep(2 * attempt)
                        continue

                    # Check if response is valid JSON
                    try:
                        data = resp.json()
                    except ValueError as e:
                        if verbose:
                            logging.warning(
                                f"Invalid JSON response: {e} (attempt {attempt}/{max_retries})"
                            )
                            logging.debug(f"Response content: {resp.text[:200]}...")
                        time.sleep(2 * attempt)
                        continue

                    items = data.get("items", [])
                    if verbose:
                        logging.info(
                            f"Page {page}: fetched {len(items)} items (total so far {len(collected)})"
                        )
                    collected.extend(items)
                    # stop early if fewer items than per_page (end reached)
                    if len(items) < self.per_page:
                        if verbose:
                            logging.info(
                                "No more pages (fewer results than per_page). Stopping."
                            )
                        page = self.max_pages  # break outer loop
                    break  # success, leave retry loop
                except requests.RequestException as e:
                    if verbose:
                        logging.warning(
                            f"Request error: {e} (attempt {attempt}/{max_retries})"
                        )
                    time.sleep(1.5 * attempt)
            else:
                logging.error(
                    f"Failed to fetch page {page} after {max_retries} attempts. Stopping."
                )
                break

            # Polite pause between pages
            if page < self.max_pages:
                sleep_s = random.uniform(*pause_range)
                if verbose:
                    logging.debug(f"Sleeping {sleep_s:.2f}s")
                time.sleep(sleep_s)

        if save_json_path:
            try:
                with open(save_json_path, "w", encoding="utf-8") as f:
                    json.dump(collected, f, ensure_ascii=False, indent=2)
                if verbose:
                    logging.info(f"Saved {len(collected)} items to {save_json_path}")
            except OSError as e:
                logging.error(f"Could not save JSON file: {e}")

        return collected

    def save_scrapped_data(self, data: pd.DataFrame) -> None:
        """Save scrapped data to a CSV file"""
        try:
            os.makedirs(self.local_save_path, exist_ok=True)
            data.to_csv(
                os.path.join(self.local_save_path, "scrapped_data.csv"), index=False
            )
        except Exception as e:
            logging.error(f"Could not save data: {e}")
            return None

    @staticmethod
    def extract_minimal_item_fields(
        items: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Return a list of dicts containing only the requested fields for each item.
        Fields kept:
        - id
        - title
        - path
        - user_id (from user.id)
        - url
        - size_title
        - photo_url (from photo.url)
        - total_item_price_amount
        - total_item_price_currency
        - status
        - item_box_first_line
        - item_box_second_line
        - item_box_accessibility_label
        """
        minimal: List[Dict[str, Any]] = []
        for it in items:
            user = it.get("user") or {}
            photo = it.get("photo") or {}
            tip = it.get("total_item_price") or {}
            box = it.get("item_box") or {}
            minimal.append(
                {
                    "ID": it.get("id"),
                    "TITLE": it.get("title"),
                    "PATH": it.get("path"),
                    "USER_ID": user.get("id"),
                    "URL": it.get("url"),
                    "PHOTO_URL": photo.get("url"),
                    "SIZE": it.get("size_title"),
                    "TOTAL_ITEM_PRICE_AMOUNT": tip.get("amount"),
                    "TOTAL_ITEM_PRICE_CURRENCY": tip.get("currency_code"),
                    "STATUS": it.get("status"),
                    "BRAND": box.get("first_line"),
                    "DESCRIPTION": box.get("accessibility_label"),
                }
            )
        return minimal


def main():
    """CLI interface for the scraper"""
    parser = argparse.ArgumentParser(description="Vinted Fashion Scraper")
    parser.add_argument(
        "--save_data_locally",
        type=bool,
        default=True,
        help="Saves scrapped data locally",
    )
    parser.add_argument(
        "--load_data_path",
        default="data/scrapped/scrapped_data.csv",
        help="Load existing data from CSV instead of scraping",
    )

    args = parser.parse_args()

    # Initialize scraper
    scrapper = VintedScraper()

    if args.load_data_path:
        # Load existing data from CSV instead of Scrapping - for tests purposes
        logger.info(f"Loading existing data from {args.load_data_path}...")
        try:
            items_df = pd.read_csv(args.load_data_path)
            logger.info(f"Loaded {len(items_df)} items from existing data")
        except FileNotFoundError:
            logger.error(f"Data file not found: {args.load_data_path}")
            return 1
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return 1
    else:
        # Scrape items from Vinted
        logger.info("Scraping items from Vinted...")
        raw_items = scrapper.fetch_vinted_items_fr(verbose=True)

        if not raw_items:
            logger.warning("No items scraped")
            return 0

        logger.info(f"Scraped {len(raw_items)} raw items")

        # Extract minimal fields
        minimal_items = scrapper.extract_minimal_item_fields(raw_items)
        items_df = pd.DataFrame(minimal_items)

        if args.save_data_locally:
            logger.info("Saving items locally...")
            scrapper.save_scrapped_data(items_df)
            logger.info("Items saved locally")

    # Save the processed data for embedding
    logger.info(f"Processed {len(items_df)} items")
    return 0


if __name__ == "__main__":
    main()
