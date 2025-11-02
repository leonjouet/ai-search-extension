import os
import torch
import json
import re
import numpy
import logging
from io import BytesIO
from typing import List, Dict, Any, Optional, Union
import requests
import pandas as pd
from PIL import Image, ImageFile, ImageOps
from transformers import CLIPProcessor, CLIPModel

# from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm
import cloudscraper
from typing import List, Union, Optional, Dict, Any, Iterable

from config import get_config

config = get_config()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ImageEmbedder:
    """Class to embedd data from vintedd and load embeddings into vector db"""

    def __init__(
        self,
        model_path: str = config["model_path"],
        chroma_path: str = config["chroma_db_path"],
    ):
        self.model_path = model_path
        self.chroma_path = chroma_path
        self.model = None
        self.client = None
        self.collection = None

    def initialize_model(self):
        """Initialize CLIP model locally"""
        try:
            logger.info("Loading local CLIP model...")
            self.processor = CLIPProcessor.from_pretrained(
                self.model_path, local_files_only=True
            )
            self.model = CLIPModel.from_pretrained(
                self.model_path, local_files_only=True
            )
            logger.info("Model loaded successfully from local path")
        except Exception as e:
            logger.error(f"Failed to load local CLIP model: {e}")
            raise

    def initialize_database(self, collection_name: str = "vinted_dresses_db"):
        """Initialize ChromaDB client and collection"""
        try:
            os.makedirs(self.chroma_path, exist_ok=True)
            logger.info("Connecting to ChromaDB...")
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_or_create_collection(
                collection_name, metadata={"hnsw:space": "cosine"}
            )
            logger.info(
                f"ChromaDB connected. Collection has {self.collection.count()} items"
            )
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def process_batch_embeddings(
        self, items_df: pd.DataFrame, batch_size: int = 6
    ) -> int:
        """
        Process embeddings for a batch of items and store them in ChromaDB.
        - Handles invalid or corrupt images safely.
        - Forces consistent image size and mode (RGB, 224x224).
        - Processes data in batches for efficiency.
        """
        if self.model is None or self.collection is None:
            raise RuntimeError("Model and database must be initialized first.")

        added_count = 0
        total_items = len(items_df)
        logger.info(f"Processing {total_items} items in batches of {batch_size}")

        for start_idx in tqdm(
            range(0, total_items, batch_size), desc="Processing batches"
        ):
            end_idx = min(start_idx + batch_size, total_items)
            batch = items_df.iloc[start_idx:end_idx]

            images, ids, metadatas = [], [], []

            # --- Load and preprocess images ---
            for _, row in batch.iterrows():
                image_url = row.get("PHOTO_URL")
                item_id = str(row.get("ID"))

                if (
                    not image_url
                    or pd.isna(image_url)
                    or not item_id
                    or item_id == "nan"
                ):
                    continue

                try:
                    response = requests.get(image_url, timeout=8)
                    if response.status_code != 200:
                        continue

                    # Open, fix EXIF rotation, ensure RGB and resize
                    ImageFile.LOAD_TRUNCATED_IMAGES = (
                        True  # allows loading incomplete images
                    )

                    image = Image.open(BytesIO(response.content))
                    image.load()
                    image = (
                        ImageOps.exif_transpose(image).convert("RGB").resize((224, 224))
                    )

                    images.append(image)
                    ids.append(item_id)
                    metadatas.append(
                        {
                            "title": row.get("TITLE", ""),
                            "price": row.get("TOTAL_ITEM_PRICE_AMOUNT"),
                            "currency": row.get("TOTAL_ITEM_PRICE_CURRENCY", "EUR"),
                            "url": row.get("URL", ""),
                            "image_url": image_url,
                            "size": row.get("SIZE", ""),
                            "brand": row.get("BRAND", ""),
                        }
                    )

                except Exception as e:
                    logger.warning(f"Error loading image for item {item_id}: {e}")
                    continue

            if not images:
                logger.warning(f"No valid images in batch {start_idx}-{end_idx}")
                continue

            try:
                # --- Create CLIP embeddings ---
                inputs = self.processor(
                    images=images, return_tensors="pt"
                )  # consistent batch
                with torch.no_grad():
                    outputs = self.model.get_image_features(**inputs)
                    embeddings = outputs.cpu().tolist()

                # --- Store in ChromaDB ---
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )

                added_count += len(ids)
                logger.info(
                    f"Added {len(ids)} items to database (total so far: {added_count})"
                )

            except Exception as e:
                logger.error(f"Error processing batch {start_idx}-{end_idx}: {e}")
                continue

        logger.info(f"Completed embedding generation. Added {added_count} items total.")
        return added_count

    def embedd_data(
        self,
        items_df: pd.DataFrame,
    ) -> int:
        """Main function to create embeddings"""

        # Initialize components
        self.initialize_model()
        self.initialize_database(collection_name="vinted_dresses_db")

        # Remove duplicates and invalid items
        items_df = items_df.dropna(subset=["ID", "PHOTO_URL"])
        items_df = items_df.drop_duplicates(subset=["ID"])

        logger.info(f"Processing {len(items_df)} valid items")

        # Check existing items to avoid duplicates
        existing_ids = set()
        try:
            existing_items = self.collection.get(include=["metadatas"])
            existing_ids = set(existing_items["ids"])
            logger.info(f"Found {len(existing_ids)} existing items in database")
        except Exception as e:
            logger.warning(f"Could not check existing items: {e}")

        # Filter out existing items
        new_items_df = items_df[~items_df["ID"].astype(str).isin(existing_ids)]
        logger.info(f"Processing {len(new_items_df)} new items")

        if len(new_items_df) == 0:
            logger.info("No new items to process")
            return 0

        # Process embeddings
        new_items_df = items_df  # For now, process all items
        added_count = self.process_batch_embeddings(new_items_df, batch_size=6)

        logger.info(f"Successfully added {added_count} new items to database")
        logger.info(f"Total items in database: {self.collection.count()}")

        return added_count

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar items using text query"""
        if self.model is None or self.collection is None:
            raise RuntimeError("Model and database must be initialized first")

        try:
            # Encode the query text using the CLIP model
            inputs = self.processor(text=[query], return_tensors="pt", padding=True)

            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                query_embedding = text_features[0].cpu().tolist()

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "distances"],
            )

            # Format results
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for item_id, distance, metadata in zip(
                    results["ids"][0], results["distances"][0], results["metadatas"][0]
                ):
                    similarity = 1 - distance if distance <= 1 else 0
                    search_results.append(
                        {
                            "id": item_id,
                            "title": metadata.get("title", ""),
                            "price": metadata.get("price"),
                            "currency": metadata.get("currency", "EUR"),
                            "url": metadata.get("url", ""),
                            "image_url": metadata.get("image_url", ""),
                            "similarity": round(similarity, 3),
                        }
                    )

            return search_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
