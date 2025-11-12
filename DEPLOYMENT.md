# Oil GNN Prediction API - Deployment Guide

## Architecture Overview

This API service provides real-time oil price predictions using a Hierarchical Temporal-Graph Model trained on GDELT news data and oil price data.

### Components

- **FastAPI Backend**: REST API for predictions and country contribution analysis
- **Model Inference**: Loads trained models from GCS and runs predictions
- **Data Loader**: Fetches and preprocesses latest GDELT data from GCS
- **Docker Container**: Production-ready containerized deployment

## API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "python_version": "3.11"
}
```

### `POST /predict`
Get oil price prediction for the latest available date

**Response:**
```json
{
  "date": "2025-11-04",
  "predicted_delta": 0.25,
  "predicted_direction": "UP",
  "top_contributors": {
    "SAU": {
      "contribution": 0.178630,
      "percentage": 29.6,
      "raw_prediction": 0.35,
      "attention_weight": 0.51
    },
    "IRN": {
      "contribution": 0.150445,
      "percentage": 24.9,
      "raw_prediction": 0.29,
      "attention_weight": 0.52
    }
  },
  "total_abs_contribution": 0.603978,
  "num_countries": 45,
  "model_version": "run_20251101_090727_18dd2c"
}
```

### `GET /contributors`
Get detailed country contribution breakdown

## Deployment Options

### Option 1: Cloud Run

**Prerequisites:**
- GCP project with billing enabled
- gcloud CLI installed and configured
- Docker installed locally

**Steps:**

1. Set environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export SERVICE_NAME="oil-gnn-api"
export DOCKER_REPO="oil-gnn-repo"
```

2. Create Artifact Registry repository:
```bash
gcloud artifacts repositories create $DOCKER_REPO \
  --repository-format=docker \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID
```

3. Deploy using the script:
```bash
./deploy_cloudrun.sh
```

### Option 2: GCP Compute Engine VM

**Prerequisites:**
- GCP project with Compute Engine API enabled
- Service account with Storage Object Viewer permissions

**Steps:**

1. Create a VM instance:
```bash
gcloud compute instances create oil-gnn-vm \
  --project=$GCP_PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --scopes=storage-ro
```

2. SSH into the VM:
```bash
gcloud compute ssh oil-gnn-vm --zone=us-central1-a
```

3. Install Docker:
```bash
sudo apt-get update
sudo apt-get install -y docker.io git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

4. Clone and deploy:
```bash
git clone https://github.com/FINTECH2526-OIL/oil-gnn-prediction.git
cd oil-gnn-prediction
git checkout Deployment

docker build -t oil-gnn-api .
docker run -d -p 8080:8080 \
  -e GCS_BUCKET_NAME=gdelt_raw_3_years \
  -e GCS_PROCESSED_PATH=processed_data/ \
  -e GCS_MODELS_PATH=trained_models/ \
  -e MODEL_RUN_ID=run_20251101_090727_18dd2c \
  --name oil-gnn-api \
  oil-gnn-api
```

5. Configure firewall:
```bash
gcloud compute firewall-rules create allow-oil-api \
  --allow tcp:8080 \
  --source-ranges 0.0.0.0/0 \
  --target-tags oil-api
  
gcloud compute instances add-tags oil-gnn-vm \
  --tags oil-api \
  --zone us-central1-a
```

## Environment Variables

- `GCS_BUCKET_NAME`: GCS bucket containing data (default: gdelt_raw_3_years)
- `GCS_PROCESSED_PATH`: Path to processed data (default: processed_data/)
- `GCS_MODELS_PATH`: Path to trained models (default: trained_models/)
- `MODEL_RUN_ID`: Specific model run to use (default: run_20251101_090727_18dd2c)
- `PREDICTION_TEMPERATURE`: Temperature for attention weights (default: 0.25)
- `TOP_COUNTRIES_COUNT`: Number of top contributors to return (default: 15)
- `PORT`: API port (default: 8080)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON (for local development)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up service account credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

3. Run locally:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

4. Test the API:
```bash
curl http://localhost:8080/
curl -X POST http://localhost:8080/predict
curl http://localhost:8080/contributors
```

## Testing the Deployed API

```bash
# Get service URL (Cloud Run)
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $GCP_REGION \
  --format 'value(status.url)')

# Health check
curl $SERVICE_URL/

# Get prediction
curl -X POST $SERVICE_URL/predict

# Get contributors
curl $SERVICE_URL/contributors
```

## Model Update Process

To update to a new trained model:

1. Train your model and upload artifacts to GCS
2. Note the new run ID (e.g., `run_20251104_120000_abc123`)
3. Update environment variable:
   - Cloud Run: Update service with new `MODEL_RUN_ID`
   - VM: Restart container with new environment variable

```bash
# Cloud Run
gcloud run services update $SERVICE_NAME \
  --update-env-vars MODEL_RUN_ID=run_20251104_120000_abc123 \
  --region $GCP_REGION

# VM
docker stop oil-gnn-api
docker rm oil-gnn-api
docker run -d -p 8080:8080 \
  -e MODEL_RUN_ID=run_20251104_120000_abc123 \
  -e GCS_BUCKET_NAME=gdelt_raw_3_years \
  --name oil-gnn-api \
  oil-gnn-api
```

## Monitoring

### Cloud Run
- View logs: `gcloud run services logs read $SERVICE_NAME --region $GCP_REGION`
- Monitor metrics in GCP Console > Cloud Run > [Service] > Metrics

### VM
- View logs: `docker logs -f oil-gnn-api`
- SSH and check: `gcloud compute ssh oil-gnn-vm --zone=us-central1-a`

## Troubleshooting

### Model not loading
- Verify GCS permissions for service account
- Check MODEL_RUN_ID matches uploaded artifacts
- Verify bucket name and paths are correct

### Out of memory
- Increase memory allocation (Cloud Run: --memory 8Gi)
- For VM: Use larger machine type

### Slow predictions
- Check data size in GCS
- Increase CPU allocation
- Consider caching preprocessed data

## Security Notes

- Service account needs only Storage Object Viewer permissions
- For production, restrict API access using Cloud Run IAM or API Gateway
- Never commit credentials or .tfvars files to git
- Use Secret Manager for sensitive configuration

## Cost Optimization

- Cloud Run: Scales to zero when not in use
- VM: Stop when not needed or use scheduled start/stop
- Use preemptible VMs for development
- Monitor GCS egress costs
