#!/bin/bash
FRONTEND_SERVICE_NAME=${SERVICE_NAME:-"oil-gnn-frontend"}
BACKEND_SERVICE_NAME=${SERVICE_NAME:-"oil-gnn-backend"}
REPO_NAME=${REPO_NAME:-"cr-repo"}
PROJECT_ID=${PROJECT_ID:-"project-00fb6cfc-5a3c-42e1-b97"}
PROJECT_REGION=${PROJECT_REGION:-"us-central1"}
FRONTEND_BUILD_PATH=${FRONTEND_BUILD_PATH:-"../gnn-frontend"}
BACKEND_BUILD_PATH=${BACKEND_BUILD_PATH:-"../"} # As dockerfile for backend is at root level

# $1 is the service account key

cat $1 | docker login -u _json_key --password-stdin https://$PROJECT_REGION-docker.pkg.dev

FRONTEND_IMAGE_TAG="$PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$FRONTEND_SERVICE_NAME"
BACKEND_IMAGE_TAG="$PROJECT_REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$BACKEND_SERVICE_NAME"

export BACKEND_URL=$(terraform output -raw model_service_url)
if [ "$2" -ne 2 ]; then
docker build -t oil_app_frontend "$FRONTEND_BUILD_PATH" --platform linux/amd64 --build-arg VITE_API_URL="$BACKEND_URL"
docker tag oil_app_frontend "$FRONTEND_IMAGE_TAG"
docker push "$FRONTEND_IMAGE_TAG" 
fi

docker build -t oil_app_backend "$BACKEND_BUILD_PATH" --platform linux/amd64
docker tag oil_app_backend "$BACKEND_IMAGE_TAG" 
docker push "$BACKEND_IMAGE_TAG" 

if [ "$2" -eq 1 ]; then
    echo "Skipping deployment as per user request."
    return 1
fi

if [ "$2" -ne 2 ]; then
    gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image "$FRONTEND_IMAGE_TAG" \
    --platform managed \
    --region $PROJECT_REGION
fi

gcloud run deploy $BACKEND_SERVICE_NAME \
    --image "$BACKEND_IMAGE_TAG" \
    --platform managed \
    --region $PROJECT_REGION
