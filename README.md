# Vinted Fashion Recommender Chrome Extension

An AI-powered Chrome extension that uses CLIP embeddings to provide semantic fashion search on Vinted.fr. Users can describe what they're looking for in natural language and find visually similar items.

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

Run with Docker (recommended for quick start)

1. Build the backend image:

```bash
cd backend
docker build -t ai-search-backend .
```

2. Run the container (exposes port 8000):

```bash
docker run --rm -p 8000:8000 \
  -e API_KEY=dev-secret-key \
  -v $(pwd)/data/chroma:/app/data/chroma \
  -v $(pwd)/model:/app/model \
  ai-search-backend
```

Notes:
- Set `API_KEY` to a secure value for production. Requests must include `x-api-key: <your key>`.
- If you have model files locally, mount `model/` into the container. Persist Chroma data by mounting `data/chroma`.

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

See `backend/config.py` for default paths and settings. Common environment overrides:
- `API_KEY` — API key required by the backend
- `MODEL_PATH` — path to CLIP model files
- `CHROMA_DB_PATH` — path where Chroma stores data

Troubleshooting

- 401 Unauthorized: check the `x-api-key` header and `API_KEY` env var.
- No results: verify `/api/stats` shows items and that the model is loaded.
- Backend errors: check logs printed by `uvicorn` or container logs.

License and notes

This repository is a demo. Scraping third-party sites may violate terms of service — use responsibly.