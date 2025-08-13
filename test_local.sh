#!/bin/bash

# Local Testing Script for Podcast Generator API
# This script helps you test the API locally before deploying to GCP

set -e

# Move to project root (script dir is cursor/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 Testing Podcast Generator API locally..."

# Load .env if present (prefer cursor/.env)
if [ -f "$PROJECT_ROOT/cursor/.env" ]; then
    echo "🔑 Loading environment variables from cursor/.env"
    set -a
    source "$PROJECT_ROOT/cursor/.env"
    set +a
elif [ -f "$PROJECT_ROOT/.env" ]; then
    echo "🔑 Loading environment variables from .env"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r cursor/requirements.txt

# Check if credentials file exists
if [ ! -f "cursor/commute-assistant.json" ]; then
    echo "❌ Error: cursor/commute-assistant.json not found in project root: $PROJECT_ROOT"
    exit 1
fi

# Require GOOGLE_API_KEY for multi-speaker TTS via Google AI API
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY is not set. Multi-speaker TTS requires a Google AI API key."
    echo "👉 Add it to your environment or create a .env file with: GOOGLE_API_KEY=your_key_here"
    exit 1
fi

# Set environment variables for local testing
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/cursor/commute-assistant.json"
export GOOGLE_CLOUD_PROJECT="commuteassistant"
export GOOGLE_CLOUD_LOCATION="us-central1"
export PORT=8000

echo "🚀 Starting local server..."
echo "📡 API will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo "🏥 Health check at: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server
cd cursor && python -m app.main
