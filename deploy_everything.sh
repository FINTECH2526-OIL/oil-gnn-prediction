#!/bin/bash

set -e

export GCP_PROJECT_ID=manifest-vault-470110-k5
export GCP_REGION=us-central1
export ALPHA_VANTAGE_API_KEY=WY4DN5PO5LQ3INPJ
export GCS_BUCKET_NAME=gdelt_raw_3_years
export SERVICE_NAME=oil-gnn-api
export DOCKER_REPO=oil-gnn-repo
export FUNCTION_NAME=oil-gnn-data-pipeline

echo "==================================================================="
echo "Deploying Oil GNN Prediction System"
echo "==================================================================="
echo "Project: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo "Bucket: $GCS_BUCKET_NAME"
echo ""

echo "Step 1: Configuring GCP project..."
gcloud config set project $GCP_PROJECT_ID

echo ""
echo "Step 2: Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  pubsub.googleapis.com

echo ""
echo "Step 3: Creating Artifact Registry..."
gcloud artifacts repositories create $DOCKER_REPO \
  --repository-format=docker \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID || echo "Repository already exists, continuing..."

echo ""
echo "Step 4: Creating Pub/Sub topic..."
gcloud pubsub topics create oil-gnn-daily-trigger --project=$GCP_PROJECT_ID || echo "Topic already exists, continuing..."

echo ""
echo "Step 5: Deploying Data Pipeline (Cloud Function)..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/gnn-backend"

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=scheduled_daily_update \
  --trigger-topic=oil-gnn-daily-trigger \
  --memory=2GB \
  --timeout=540s \
  --set-env-vars="GCS_BUCKET_NAME=${GCS_BUCKET_NAME},ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY},GCS_PROCESSED_PATH=processed_data/,GCS_MODELS_PATH=trained_models/" \
  --project=$GCP_PROJECT_ID

cd "$SCRIPT_DIR"

echo ""
echo "Step 6: Creating Cloud Scheduler job..."
gcloud scheduler jobs create pubsub oil-gnn-daily-data-job \
  --location=$GCP_REGION \
  --schedule="0 6 * * *" \
  --topic=oil-gnn-daily-trigger \
  --message-body='{"trigger":"daily"}' \
  --time-zone="America/New_York" \
  --project=$GCP_PROJECT_ID || \
gcloud scheduler jobs update pubsub oil-gnn-daily-data-job \
  --location=$GCP_REGION \
  --schedule="0 6 * * *" \
  --topic=oil-gnn-daily-trigger \
  --message-body='{"trigger":"daily"}' \
  --time-zone="America/New_York" \
  --project=$GCP_PROJECT_ID

echo ""
echo "Step 7: Building Docker image for Prediction API..."
FULL_IMAGE_NAME="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${DOCKER_REPO}/${SERVICE_NAME}:latest"

docker build -t ${SERVICE_NAME}:latest -f Dockerfile .
docker tag ${SERVICE_NAME}:latest ${FULL_IMAGE_NAME}

echo ""
echo "Step 8: Configuring Docker auth..."
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

echo ""
echo "Step 9: Pushing Docker image..."
docker push ${FULL_IMAGE_NAME}

echo ""
echo "Step 10: Deploying Prediction API (Cloud Run)..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${FULL_IMAGE_NAME} \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GCS_BUCKET_NAME=${GCS_BUCKET_NAME},GCS_PROCESSED_PATH=processed_data/,GCS_MODELS_PATH=trained_models/,MODEL_RUN_ID=run_20251101_090727_18dd2c" \
  --project ${GCP_PROJECT_ID}

echo ""
echo "==================================================================="
echo "DEPLOYMENT COMPLETE!"
echo "==================================================================="
echo ""
echo "Your API is now live at:"
gcloud run services describe ${SERVICE_NAME} --platform managed --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID}
echo ""
echo "Data pipeline will run daily at 6:00 AM ET"
echo ""
echo "Test your API:"
echo "  SERVICE_URL=\$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${GCP_REGION} --format 'value(status.url)')"
echo "  curl \$SERVICE_URL/health"
echo "  curl -X POST \$SERVICE_URL/predict"
echo ""
echo "Manually trigger data pipeline:"
echo "  gcloud functions call ${FUNCTION_NAME} --region=${GCP_REGION}"
echo ""
echo "View logs:"
echo "  gcloud functions logs read ${FUNCTION_NAME} --region=${GCP_REGION} --limit=50"
echo "  gcloud run services logs read ${SERVICE_NAME} --region=${GCP_REGION} --limit=50"
echo ""
echo "==================================================================="
