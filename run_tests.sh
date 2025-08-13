#!/bin/bash

# Test runner script for the Podcast Generator API

set -e

echo "🧪 Running Podcast Generator API Tests"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the cursor directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables for testing
export GOOGLE_API_KEY="test-api-key"
export GOOGLE_CLOUD_PROJECT="test-project"

# Run tests with different options
echo ""
echo "🚀 Running all tests..."
pytest tests/ -v

echo ""
echo "🔍 Running unit tests only..."
pytest tests/ -m "unit" -v

echo ""
echo "🔗 Running integration tests only..."
pytest tests/ -m "integration" -v

echo ""
echo "🌐 Running API endpoint tests only..."
pytest tests/ -m "api" -v

echo ""
echo "📊 Running tests with coverage..."
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "✅ All tests completed!"
echo ""
echo "📈 Coverage report generated in htmlcov/index.html"
echo "🎯 To run specific test files: pytest tests/test_config.py -v"
echo "🎯 To run specific test functions: pytest tests/test_config.py::TestConfig::test_default_values -v"
