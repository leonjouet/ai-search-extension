#!/usr/bin/env python3
"""
Database refresh script for Vinted Fashion search assistant backend.
"""

import os
import sys
import logging
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from scraper import VintedScraper  # noqa: E402
from embeddings import ImageEmbedder  # noqa: E402


def setup_logging(log_file: str = None):
    """Setup logging configuration"""
    log_format = "[%(asctime)s] %(levelname)s: %(message)s"

    if log_file:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)


def main():
    """Main refresh function"""
    parser = argparse.ArgumentParser(description="Refresh Vinted Fashion Database")

    parser.add_argument(
        "--log-file", default="./logs/refresh.log", help="Log file path"
    )
    parser.add_argument(
        "--save_data",
        action="store_true",
        default=False, #True,
        help="Save scraped data to CSV file",
    )
    parser.add_argument(
        "--load_data_path",
        default=None, #"data/scrapped/scrapped_data.csv",
        help="Path to existing CSV data",
    )

    args = parser.parse_args()

    # Setup logging
    os.makedirs(os.path.dirname(args.log_file), exist_ok=True)
    setup_logging(args.log_file)
    logger = logging.getLogger(__name__)

    try:
        # Initialize scraper
        scraper = VintedScraper()
        # Initialize embedder
        embedder = ImageEmbedder()

        # Get initial count
        embedder.initialize_database()
        initial_count = embedder.collection.count()
        logger.info(f"Initial database count: {initial_count}")

        # Load or scrape data
        total_added = 0

        if args.load_data_path:
            # Load existing data from CSV
            logger.info(f"Loading existing data from {args.load_data_path}...")
            try:
                items_df = pd.read_csv(args.load_data_path)
                logger.info(f"Loaded {len(items_df)} items from existing data")

                # Create embeddings and add to database
                logger.info(f"Creating embeddings for {len(items_df)} items...")
                added = embedder.embedd_data(items_df)
                total_added += added
                logger.info(f"Added {added} items from existing data")

            except FileNotFoundError:
                logger.error(f"Data file not found: {args.load_data_path}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error loading data: {e}")
                sys.exit(1)
        else:
            # Scrape items from Vinted
            logger.info(f"Scraping items from catalog {scraper}...")
            raw_items = scraper.fetch_vinted_items_fr(verbose=True)

            if not raw_items:
                logger.warning(f"No items scraped for catalog {scraper.catalog_id}")
                sys.exit(1)

            logger.info(
                f"Scraped {len(raw_items)} raw items from catalog "
                f"{scraper.catalog_id}"
            )

            # Extract minimal fields
            minimal_items = scraper.extract_minimal_item_fields(raw_items)
            items_df = pd.DataFrame(minimal_items)

            # Save data locally if requested
            if args.save_data:
                scraper.save_scrapped_data(items_df)
                logger.info("Saved scraped data to CSV")

            # Create embeddings and add to database
            logger.info(f"Creating embeddings for {len(items_df)} items...")
            added = embedder.embedd_data(items_df)
            total_added += added
            logger.info(f"Added {added} items from catalog {scraper.catalog_id}")

        # Get final count
        final_count = embedder.collection.count()
        logger.info(f"Final database count: {final_count}")
        logger.info(f"Total new items added: {total_added}")

        # Log success
        logger.info("Database refresh completed successfully")

    except Exception as e:
        logger.error(f"Database refresh failed: {e}")
        logger.exception("Full error traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
