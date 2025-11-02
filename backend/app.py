from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
from datetime import datetime

from embeddings import ImageEmbedder
from config import get_config

config = get_config()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vinted Fashion Recommender API", version="1.0.0")

# Replace with your Chrome extension ID for production:
# "chrome-extension://<your-extension-id>"
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Authentication
_raw_api_key = os.getenv("API_KEY", "dev-secret-key")

# Sanitize: remove surrounding quotes and whitespace
API_KEY = _raw_api_key.strip().strip('"').strip("'")
if API_KEY != _raw_api_key:
    logger.info(
        "Sanitized API_KEY changed from raw length %d to %d",
        len(_raw_api_key),
        len(API_KEY),
    )
logger.info(
    "Startup API_KEY (masked): %s*** (length %d)",
    API_KEY[:3],
    len(API_KEY),
)
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Validate API key from header, with detailed logging."""
    if api_key is None:
        logger.warning("Missing API key header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Missing API key",
        )
    if api_key != API_KEY:
        logger.warning(
            "Invalid API key provided: %s*** (len %d)",
            api_key[:3],

            len(api_key),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    logger.debug("API key validated successfully.")

# Global embedder instance
embedder = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    id: str

    title: str
    price: Optional[float]
    currency: Optional[str]
    url: str
    image_url: str
    similarity: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_found: int


@app.on_event("startup")
async def startup_event():
    global embedder
    try:
        embedder = ImageEmbedder(
            model_path=config["model_path"],
            chroma_path=config["chroma_db_path"],
        )
        logger.info("Initializing model and database...")
        embedder.initialize_model()
        embedder.initialize_database()
        logger.info(
            "System ready. DB has %d items.",
            embedder.collection.count(),
        )
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.get("/api/health", dependencies=[Depends(verify_api_key)])
async def health_check():
    try:
        if (
            embedder is None
            or embedder.model is None
            or embedder.collection is None
        ):
            return {
                "status": "unhealthy",
                "message": "Model or DB not initialized",
            }

        count = embedder.collection.count()
        return {
            "status": "healthy",
            "model_loaded": embedder.model is not None,
            "database_connected": embedder.collection is not None,
            "total_items": count,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/stats", dependencies=[Depends(verify_api_key)])
async def get_stats():
    try:
        if embedder is None or embedder.collection is None:
            raise HTTPException(status_code=503, detail="DB not initialized")

        count = embedder.collection.count()
        return {
            "total_items": count,
            "collection_name": "vinted_dresses_db",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/search",
    response_model=SearchResponse,
    dependencies=[Depends(verify_api_key)],
)
async def search_items(request: SearchRequest):
    try:
        if (
            embedder is None
            or embedder.model is None
            or embedder.collection is None
        ):
            raise HTTPException(
                status_code=503,
                detail="Model or DB not initialized",
            )

        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty",
            )

        logger.info(f"Searching for: {request.query}")
        results = embedder.search_similar(request.query, top_k=request.top_k)

        search_results = [
            SearchResult(
                id=str(r["id"]),
                title=r.get("title", "Unknown"),
                price=r.get("price"),
                currency=r.get("currency", "EUR"),
                url=r.get("url", ""),
                image_url=r.get("image_url", ""),
                similarity=r.get("similarity", 0.0),
            )
            for r in results
        ]

        logger.info(f"Found {len(search_results)} results")
        return SearchResponse(
            results=search_results,
            total_found=len(search_results),
        )


    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)