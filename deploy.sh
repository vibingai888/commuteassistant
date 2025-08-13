#!/bin/bash

# GCP Deployment Script for Podcast Generator API
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="commuteassistant"
SERVICE_NAME="podcast-generator-api"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting deployment to GCP Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
echo "📋 Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Load .env if present to pick up GOOGLE_API_KEY
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Build and push the Docker image using Cloud Build config
echo "🐳 Building and pushing Docker image via Cloud Build..."
gcloud builds submit --config cloudbuild.yaml --substitutions _IMAGE=$IMAGE_NAME .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."

# Prepare env vars
ENV_VARS="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION"
if [ -n "${GOOGLE_API_KEY}" ]; then
  ENV_VARS=",${ENV_VARS},GOOGLE_API_KEY=${GOOGLE_API_KEY}"
  # Trim any leading comma
  ENV_VARS="${ENV_VARS#,}"
fi

gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 900 \
    --concurrency 80 \
    --max-instances 10 \
    --set-env-vars "$ENV_VARS" \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📚 API Documentation: $SERVICE_URL/docs"
echo "🏥 Health Check: $SERVICE_URL/health"

# Test the deployment
echo "🧪 Testing the deployment..."
sleep 10  # Wait for service to be ready

if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. Service might still be starting up."
fi

echo ""
echo "🎉 Your Podcast Generator API is now deployed on GCP Cloud Run!"
echo "💡 You can now use this API in your frontend application."
