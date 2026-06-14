#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
echo "Starting Voice Emotion Backend on http://localhost:8000"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
