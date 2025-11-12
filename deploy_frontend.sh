#!/bin/bash

# Frontend Deployment Script
# Deploys the React frontend to Cloud Run for public access

set -e

# Configuration
GCP_PROJECT_ID="manifest-vault-470110-k5"
GCP_REGION="us-central1"
SERVICE_NAME="oil-gnn-frontend"
IMAGE_NAME="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/oil-gnn-repo/${SERVICE_NAME}:latest"

echo "====================================================================="
echo "Deploying Oil GNN Frontend to Cloud Run"
echo "====================================================================="
echo "Project: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")/gnn-frontend"

echo "Step 1: Building Docker image..."
docker build -t ${SERVICE_NAME}:latest -f Dockerfile .

echo ""
echo "Step 2: Tagging image..."
docker tag ${SERVICE_NAME}:latest ${IMAGE_NAME}

echo ""
echo "Step 3: Configuring Docker authentication..."
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

echo ""
echo "Step 4: Pushing image to Artifact Registry..."
docker push ${IMAGE_NAME}

echo ""
echo "Step 5: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image=${IMAGE_NAME} \
  --platform=managed \
  --region=${GCP_REGION} \
  --allow-unauthenticated \
  --port=80 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="VITE_API_URL=https://oil-gnn-api-1072886277511.us-central1.run.app" \
  --project=${GCP_PROJECT_ID}

echo ""
echo "====================================================================="
echo "Frontend Deployment Complete!"
echo "====================================================================="
echo ""
gcloud run services describe ${SERVICE_NAME} \
  --platform=managed \
  --region=${GCP_REGION} \
  --format='value(status.url)' \
  --project=${GCP_PROJECT_ID}
