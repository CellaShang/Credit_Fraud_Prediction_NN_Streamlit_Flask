#!/bin/bash
# Force Streamlit to use Cloud Run's PORT
PORT=${PORT:-8080}

# Disable CORS for Cloud Run and prevent telemetry popups
exec streamlit run streamlit_app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false

