#!/bin/sh
export PORT=${PORT:-8080}

# Run Flask app with gunicorn, binding to Cloud Run's $PORT
exec gunicorn -w 1 -b :$PORT flask_app:app
