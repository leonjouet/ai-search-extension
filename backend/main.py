from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
from embeddings import ImageEmbedder

from config import get_config
config = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vinted Fashion Recommender API", version="1.0.0")

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for embedder
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
    """Initialize the embedder on startup"""
    global embedder

    try:
        # Initialize embedder with correct paths
        embedder = ImageEmbedder(
            model_path=config["model_path"], chroma_path=config["chroma_db_path"]
        )

        logger.info("Initializing model and database...")
        embedder.initialize_model()
        embedder.initialize_database()
        logger.info(f"System ready. Database has {embedder.collection.count()} items")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        if embedder is None or embedder.model is None or embedder.collection is None:
            return {
                "status": "unhealthy",
                "message": "Model or database not initialized",
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


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        if embedder is None or embedder.collection is None:
            raise HTTPException(status_code=503, detail="Database not initialized")

        count = embedder.collection.count()
        return {
            "total_items": count,
            "collection_name": "vinted_dresses_db",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=SearchResponse)
async def search_items(request: SearchRequest):
    """Search for similar items using text query"""
    try:
        if embedder is None or embedder.model is None or embedder.collection is None:
            raise HTTPException(
                status_code=503, detail="Model or database not initialized"
            )

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Use the embedder's search functionality
        logger.info(f"Searching for: {request.query}")
        results = embedder.search_similar(request.query, top_k=request.top_k)

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=str(result["id"]),
                    title=result.get("title", "Unknown"),
                    price=result.get("price"),
                    currency=result.get("currency", "EUR"),
                    url=result.get("url", ""),
                    image_url=result.get("image_url", ""),
                    similarity=result.get("similarity", 0.0),
                )
            )

        logger.info(f"Found {len(search_results)} results")
        return SearchResponse(results=search_results, total_found=len(search_results))

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
