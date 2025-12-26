# Vinted Fashion Recommender Chrome Extension

An AI-powered Chrome extension that uses CLIP embeddings for semantic fashion search on Vinted.fr.

<video src="https://github.com/user-attachments/assets/edfb1fa0-eff6-4f0a-95c2-22cf1850c237" width="320" height="240" controls></video>

## Setup

The extension requires a backend service and a CLIP model.

### Download the CLIP Model

Download the CLIP model from Hugging Face and place it in the `model/` directory:

```bash
cd model
git clone https://huggingface.co/openai/clip-vit-base-patch32 0_CLIPModel
cd ..
```

Or download manually from: https://huggingface.co/openai/clip-vit-base-patch32

### Docker Compose (recommended)

```bash
cd backend
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f
```

Stop the container:
```bash
docker-compose down
```

### Local Development

Without Docker:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Chrome Extension

1. Go to `chrome://extensions/` and enable Developer mode.
2. Click "Load unpacked" and select the `extension/` directory.
3. Visit `https://www.vinted.fr` and use the extension.

## Configuration

Environment variables (in `docker-compose.yml` or shell):
- `API_KEY` — Authentication key (default: `dev-secret-key`)
- `API_PORT` — Server port (default: `8000`)
- `API_HOST` — Server host (default: `0.0.0.0`)
- `REFRESH_DB_ON_STARTUP` — Refresh database on startup (default: `false`)

## API

- GET `/api/health` — Health check
- GET `/api/stats` — Database statistics
- POST `/api/search` — Search endpoint (body: `{"query": "text", "top_k": 5}`)

All requests require: `x-api-key: <your-key>`

Example:
```bash
curl -H "x-api-key: dev-secret-key" http://localhost:8000/api/health
```