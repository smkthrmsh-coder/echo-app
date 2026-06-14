#!/bin/bash
set -e
cd "$(dirname "$0")/frontend"
echo "Starting Voice Emotion Frontend on http://localhost:3000"
npm run dev
