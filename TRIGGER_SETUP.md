# Cloud Build Trigger Setup Guide

## Automatic Setup via gcloud CLI

```bash
gcloud builds triggers create github \
  --name="oil-gnn-api-deployment" \
  --repo-name="oil-gnn-prediction" \
  --repo-owner="FINTECH2526-OIL" \
  --branch-pattern="^Deployment$" \
  --build-config="cloudbuild.yaml" \
  --region=us-central1
```

## Manual Setup via Google Cloud Console

### Step 1: Navigate to Cloud Build Triggers
1. Go to: https://console.cloud.google.com/cloud-build/triggers
2. Select project: `manifest-vault-470110-k5`
3. Click "CREATE TRIGGER"

### Step 2: Trigger Configuration

**Name:** `oil-gnn-api-deployment`

**Description:** Auto-deploy oil-gnn-api on push to Deployment branch

**Event:** Push to a branch

**Source:**
- Repository provider: GitHub
- Repository: `FINTECH2526-OIL/oil-gnn-prediction`
- Branch: `^Deployment$` (regex)

**Configuration:**
- Type: Cloud Build configuration file (yaml or json)
- Location: Repository
- Cloud Build configuration file location: `/cloudbuild.yaml`

**Advanced (optional):**
- Machine type: e2-highcpu-8
- Timeout: 20m (1200s)

**Service Account:**
- Use default Compute Engine service account
- Or create dedicated service account with these roles:
  - Cloud Run Admin
  - Service Account User
  - Storage Admin
  - Artifact Registry Writer

### Step 3: Required Permissions

The service account needs:
```
roles/run.admin
roles/iam.serviceAccountUser  
roles/storage.admin
roles/artifactregistry.writer
roles/cloudbuild.builds.builder
```

Grant permissions:
```bash
PROJECT_ID="manifest-vault-470110-k5"
PROJECT_NUMBER="1072886277511"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### Step 4: Connect GitHub Repository

If not already connected:
1. In Cloud Build Triggers page, click "CONNECT REPOSITORY"
2. Select source: GitHub
3. Authenticate with GitHub
4. Select repository: `FINTECH2526-OIL/oil-gnn-prediction`
5. Click "CONNECT"

### Step 5: Test the Trigger

After setup, test by:
```bash
git commit --allow-empty -m "test: trigger deployment"
git push origin Deployment
```

Monitor at: https://console.cloud.google.com/cloud-build/builds

## What the Trigger Does

When you push to the `Deployment` branch:

1. **Build Docker Image** - Uses Dockerfile in repo root
2. **Tag Image** - Tags with both `:latest` and `:$SHORT_SHA`
3. **Push to Artifact Registry** - Pushes to `us-central1-docker.pkg.dev/.../oil-gnn-api`
4. **Deploy to Cloud Run** - Updates `oil-gnn-api` service with new image
5. **Auto-updates** - Service gets new revision automatically

## Build Time

Expected: 5-10 minutes per deployment

## Environment Variables Set

The Cloud Run service will have:
- `ALPHA_VANTAGE_API_KEY=WY4DN5PO5LQ3INPJ`
- `GCS_BUCKET_NAME=gdelt_raw_3_years`
- `GCP_PROJECT_ID=manifest-vault-470110-k5`

## Monitoring

View builds: https://console.cloud.google.com/cloud-build/builds?project=manifest-vault-470110-k5

View service: https://console.cloud.google.com/run/detail/us-central1/oil-gnn-api?project=manifest-vault-470110-k5

## Troubleshooting

### Build fails: "permission denied"
Grant service account the required roles (see Step 3)

### Build fails: "repository not found"
Check GitHub connection (see Step 4)

### Build succeeds but deployment fails
Check Cloud Run service account has permission to pull from Artifact Registry

### Want to deploy manually
```bash
gcloud builds submit --config cloudbuild.yaml
```
