#!/bin/bash
SERVICE_NAME=${SERVICE_NAME:-"INSERT_VALUE_HERE"}
REPO_NAME=${REPO_NAME:-"INSERT_VALUE_HERE"}
PROJECT_ID=${PROJECT_ID:-"INSERT_VALUE_HERE"}
PROJECT_REGION=${PROJECT_REGION:-"INSERT_VALUE_HERE"}
BUILD_PATH=${BUILD_PATH:-"INSERT_VALUE_HERE"}

# cat manifest-vault-470110-k5-3edc451d98b8.json | docker login -u _json_key --password-stdin https://$PROJECT_REGION-docker.pkg.dev

IMAGE_TAG="$PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME"

docker build -t oil_app_image "$BUILD_PATH" --platform linux/amd64
docker tag oil_app_image "$IMAGE_TAG" 
docker push "$IMAGE_TAG" 

gcloud run deploy $SERVICE_NAME \
    --image "$IMAGE_TAG" \
    --platform managed \
    --region $PROJECT_REGION
