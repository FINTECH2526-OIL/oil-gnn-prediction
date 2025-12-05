#!/bin/bash

set -e

echo "Starting Oil GNN Prediction API..."

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "Set it with: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
    exit 1
fi

if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Error: Credentials file not found at $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

cd gnn-backend

echo "Starting server on http://0.0.0.0:8080"
echo "API endpoints:"
echo "  GET  http://localhost:8080/"
echo "  POST http://localhost:8080/predict"
echo "  GET  http://localhost:8080/contributors"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
