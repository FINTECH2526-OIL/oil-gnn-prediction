# Deployment Guide

## Issue: Cloud Function 403 Forbidden

The Cloud Function is configured with **Pub/Sub trigger only**, not HTTP trigger. This is intentional for security - it should only be triggered by Cloud Scheduler.

### Solution Options:

#### Option 1: Trigger via Pub/Sub (Recommended)
```bash
gcloud pubsub topics publish oil-gnn-daily-trigger \
  --message='{"trigger":"manual_test"}' \
  --project=manifest-vault-470110-k5
```

#### Option 2: Check Cloud Scheduler
The scheduler runs automatically at **7:15 AM SGT (Tue-Sat)**. To run it manually:
```bash
gcloud scheduler jobs run oil-gnn-daily-data-job \
  --location=us-central1 \
  --project=manifest-vault-470110-k5
```

#### Option 3: Add HTTP Trigger (Not Recommended for Production)
If you need HTTP access for testing, redeploy with:
```bash
gcloud functions deploy oil-gnn-data-pipeline \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./gnn-backend \
  --entry-point=daily_data_update \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=540s \
  --project=manifest-vault-470110-k5
```

---

## Frontend Deployment

### Step 1: Make deploy script executable
```bash
chmod +x deploy_frontend.sh
```

### Step 2: Deploy frontend to Cloud Run
```bash
./deploy_frontend.sh
```

This will:
1. Build the React/Vite app
2. Create a Docker image with nginx
3. Push to Artifact Registry
4. Deploy to Cloud Run with **public access** (--allow-unauthenticated)
5. Output the public URL

### Step 3: Access your frontend
After deployment, you'll get a URL like:
```
https://oil-gnn-frontend-1072886277511.us-central1.run.app
```

---

## Alternative: Use GitHub Cloud Build Trigger

Since you have Cloud Build set up, you can also trigger builds via GitHub:

1. **Push to GitHub** - Cloud Build automatically builds and deploys
2. **Check build status** at your Cloud Build console
3. **Frontend URL** will be available after deployment

---

## Testing the Full Pipeline

### 1. Check if prediction history exists
```bash
curl https://oil-gnn-api-1072886277511.us-central1.run.app/history
```

### 2. Generate a prediction manually
```bash
curl -X POST https://oil-gnn-api-1072886277511.us-central1.run.app/predict
```

### 3. Run data pipeline (via Pub/Sub)
```bash
gcloud pubsub topics publish oil-gnn-daily-trigger \
  --message='{"trigger":"manual"}' \
  --project=manifest-vault-470110-k5
```

### 4. Check Cloud Function logs
```bash
gcloud functions logs read oil-gnn-data-pipeline \
  --region=us-central1 \
  --limit=50 \
  --project=manifest-vault-470110-k5
```

---

## Summary

**Current Status:**
✅ Backend API deployed and working
✅ Scheduler configured (7:15 AM SGT, Tue-Sat)
✅ Cloud Function deployed (Pub/Sub trigger only)
⏳ Frontend needs deployment

**Next Steps:**
1. Run `./deploy_frontend.sh` to deploy frontend publicly
2. Access the frontend URL to view the dashboard
3. Wait for scheduler to run OR manually trigger via Pub/Sub
4. Check `/history` endpoint after first pipeline run

**Frontend Features:**
- Dashboard with prediction charts (predicted vs actual)
- Network graph visualization of country contributions
- Date range filtering (7/14/30/60/90 days)
- Real-time API status indicator
- Top contributors table with detailed metrics
