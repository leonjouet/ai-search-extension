# Vinted Fashion Recommender Chrome Extension

An AI-powered Chrome extension that uses CLIP embeddings to provide semantic fashion search on Vinted.fr. Users can describe what they're looking for in natural language and find visually similar items.

<video src="https://github.com/user-attachments/assets/edfb1fa0-eff6-4f0a-95c2-22cf1850c237" width="320" height="240" controls></video>

Repository layout
- `backend/` - FastAPI backend that loads a CLIP model, stores embeddings in Chroma, and exposes search endpoints.
- `extension/` - Chrome extension (Manifest V3) that calls the backend and injects a search UI into `vinted.fr` pages.
- `model/` - Optional model files (large; may be provided separately).

Summary
- Backend: `backend/app.py` (FastAPI). Start with `uvicorn app:app` from the `backend` folder.
- Extension: load `extension/` as an unpacked extension in Chrome.
- The API requires an API key via the header `x-api-key`. Default is `dev-secret-key` unless you set `API_KEY` in the environment.

User experience

- Install and start the backend (Docker or locally). The backend must be reachable from your browser (default: `http://localhost:8000`).
- Load the Chrome extension (`extension/`) as an unpacked extension.
- On Vinted (`https://www.vinted.fr`), open the extension UI or use the injected floating search button.
- Type a natural-language description (for example: "red floral summer dress" or "vintage denim jacket") and submit.
- The extension sends the query to the backend (including `x-api-key`). The backend returns visually similar items based on CLIP embeddings.
- Click any result to open the original Vinted listing in a new tab.

Typical user goals covered:
- Rapidly find items that match a visual/style description.
- Browse results without leaving Vinted.
- Open and inspect matching listings in new tabs.

Run with Docker Compose (recommended)

1. Build and start the container:

```bash
cd backend
docker-compose up -d --build
```

2. View logs:

```bash
docker-compose logs -f
```

3. Stop the container:

```bash
docker-compose down
```

Configuration options in `docker-compose.yml`:
- `API_KEY` — Set to a secure value for production (default: `dev-secret-key`)
- `API_HOST` — Server host (default: `0.0.0.0`)
- `API_PORT` — Server port (default: `8000`)
- `REFRESH_DB_ON_STARTUP` — Set to `true` to refresh ChromaDB on container startup (default: `false`)
- `REFRESH_DATA_PATH` — Path to CSV data for database refresh (default: `data/scrapped/scrapped_data.csv`)

The Docker setup mounts volumes for:
- `model/` — CLIP model files (mounted to keep image lightweight)
- `data/chroma/` — ChromaDB persistence
- `data/scrapped/` — Scraped data storage
- `logs/` — Application logs

Run with Docker (manual)

Alternatively, you can build and run manually:

```bash
cd backend
docker build -t vinted-backend .
docker run -d -p 8000:8000 \
  -e API_KEY=dev-secret-key \
  -v $(pwd)/model:/app/model \
  -v $(pwd)/data/chroma:/app/data/chroma \
  -v $(pwd)/data/scrapped:/app/data/scrapped \
  -v $(pwd)/logs:/app/logs \
  vinted-backend
```

Run locally (without Docker)

1. Create and activate a virtual environment, then install dependencies:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. (Optional) Set environment variables to override defaults:

```bash
export API_KEY=dev-secret-key
export MODEL_PATH=$(pwd)/../model/0_CLIPModel
export CHROMA_DB_PATH=$(pwd)/data/chroma
```

3. Start the server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Chrome extension (install)

1. Open Chrome and go to `chrome://extensions/`.
2. Enable Developer mode.
3. Click "Load unpacked" and select the `extension/` directory.
4. Visit `https://www.vinted.fr` and use the extension UI.

By default the extension expects the backend at `http://localhost:8000`. Update the extension settings or source if you run the backend on a different host/port.

API quick reference

- GET /api/health — health and model/db status
- GET /api/stats — database stats
- POST /api/search — body: {"query": "text", "top_k": 5}

All requests require the header `x-api-key: <your key>`.

Example curl requests

```bash
curl -H "x-api-key: dev-secret-key" http://localhost:8000/api/health

curl -H "Content-Type: application/json" \
  -H "x-api-key: dev-secret-key" \
  -d '{"query":"red dress","top_k":5}' \
  http://localhost:8000/api/search
```

Configuration

The backend is configured via `backend/config.py`, which provides default values for all settings. Most settings can be overridden using environment variables.

### Core Configuration (`config.py`)

**Paths:**
- `MODEL_PATH` — Path to CLIP model files (default: `model/0_CLIPModel/`)
- `CHROMA_DB_PATH` — ChromaDB storage location (default: `data/chroma`)
- `COLLECTION_NAME` — ChromaDB collection name (default: `vinted_dresses_db`)
- `LOCAL_SAVE_PATH` — Path for scraped data storage (default: `data/scrapped/`)

**API Settings:**
- `API_HOST` — Server bind address (default: `0.0.0.0`)
- `API_PORT` — Server port (default: `8000`)
- `API_WORKERS` — Number of Uvicorn workers (default: `1`)
- `API_KEY` — Authentication key (set via environment variable, default: `dev-secret-key`)

**Scraping Settings:**
- `VINTED_BASE_URL` — Vinted API base URL (default: `https://www.vinted.fr`)
- `DEFAULT_CATALOG_ID` — Default category to scrape (default: `10` for dresses)
- `MAX_PAGES` — Maximum pages to scrape per run (default: `5`)
- `ITEMS_PER_PAGE` — Items per page (default: `96`)
- `BATCH_SIZE` — Embedding processing batch size (default: `6`)
- `PAUSE_RANGE` — Random pause between requests in seconds (default: `1.0-2.5`)

**Database Refresh (Docker only):**
- `REFRESH_DB_ON_STARTUP` — Refresh ChromaDB when container starts (default: `false`)
- `REFRESH_DATA_PATH` — CSV file to load for database refresh (default: `data/scrapped/scrapped_data.csv`)

### Environment Variable Overrides

All settings in `config.py` can be overridden via environment variables. Common overrides:

```bash
export API_KEY=your-secure-key-here
export API_PORT=8080
export MAX_PAGES=10
export CHROMA_DB_PATH=/custom/path/to/chroma
```

Or in `docker-compose.yml`:

```yaml
environment:
  - API_KEY=your-secure-key
  - API_PORT=8080
  - REFRESH_DB_ON_STARTUP=true
```

See `backend/config.py` for the complete list of configurable settings.

Troubleshooting

- 401 Unauthorized: check the `x-api-key` header and `API_KEY` env var.
- No results: verify `/api/stats` shows items and that the model is loaded.
- Backend errors: check logs printed by `uvicorn` or container logs.

License and notes

This repository is a demo. Scraping third-party sites may violate terms of service — use responsibly.