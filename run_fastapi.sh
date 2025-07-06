#!/bin/bash
# Script to run the FastAPI server

echo "Starting RAG-YouTube FastAPI server..."
echo "======================================="
echo ""
echo "The server will be available at:"
echo "  - Web UI: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - OpenAPI: http://localhost:8000/openapi.json"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Change to the project directory
cd "$(dirname "$0")"

# Run the FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000