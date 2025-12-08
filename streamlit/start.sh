#!/bin/sh
set -e

export PORT=${PORT:-8080}

echo "Starting Streamlit on port $PORT..."

exec streamlit run streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=$PORT \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.enableWebsocketCompression=false \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false
