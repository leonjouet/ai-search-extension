#!/bin/bash
set -e

# Check if database refresh is requested
if [ "$REFRESH_DB_ON_STARTUP" = "True" ]; then
    echo "Refresh or create ChromaDB before starting server..."
    python refresh_database.py
    echo "Database refresh completed"
fi

# Get API configuration from environment or use defaults from config.py
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"

echo "Starting FastAPI server on ${API_HOST}:${API_PORT}..."

# Start the FastAPI server with configured host and port
exec uvicorn app:app --host "$API_HOST" --port "$API_PORT"