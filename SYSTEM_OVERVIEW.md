# Complete System Overview

## You Now Have 2 Deployments

### 1. Daily Data Pipeline (NEW!)
**Automatically fetches and processes fresh data every day**

```
Cloud Scheduler (6 AM ET daily)
    ↓
Cloud Function (data pipeline)
    ↓ Fetches
GDELT News + Alpha Vantage Oil Prices
    ↓ Processes
Feature Engineering (same as training)
    ↓ Saves
GCS Bucket: processed_data/final_aligned_data_YYYYMMDD.json.gz
```

**Deploy:**
```bash
export ALPHA_VANTAGE_API_KEY="your-free-api-key"
./deploy_data_pipeline.sh
```

**Cost:** ~$1/month  
**Runs:** Automatically every day at 6 AM ET  
**See:** DATA_PIPELINE.md for complete details

---

### 2. Prediction API
**Serves predictions via REST API**

```
User Request
    ↓
POST /predict (Cloud Run)
    ↓ Loads
Latest data from GCS (auto-updated daily by pipeline)
    ↓ Loads
Trained models from GCS
    ↓ Runs
Hierarchical Temporal-Graph Model
    ↓ Returns
Prediction + Country Contributions
```

**Deploy:**
```bash
./deploy_cloudrun.sh
```

**Cost:** ~$10-50/month  
**Scales:** Automatically based on traffic  
**See:** QUICKSTART.md for deployment

---

## Complete Data Flow

```
DAY 1: Setup
┌─────────────────────────────────────────────────────┐
│ 1. Deploy Data Pipeline (Cloud Function)           │
│    ./deploy_data_pipeline.sh                       │
│                                                      │
│ 2. Deploy Prediction API (Cloud Run)               │
│    ./deploy_cloudrun.sh                            │
└─────────────────────────────────────────────────────┘

EVERY DAY: Automatic Updates
┌─────────────────────────────────────────────────────┐
│ 6:00 AM ET: Cloud Scheduler triggers                │
│    ↓                                                 │
│ Cloud Function runs:                                │
│    → Fetch GDELT news (last 24 hours)              │
│    → Fetch oil prices from Alpha Vantage           │
│    → Process & engineer features                    │
│    → Save to GCS: final_aligned_data_YYYYMMDD.gz   │
│    ↓                                                 │
│ GCS now has fresh data                              │
└─────────────────────────────────────────────────────┘

ANYTIME: User Requests
┌─────────────────────────────────────────────────────┐
│ User calls: POST /predict                           │
│    ↓                                                 │
│ Cloud Run API:                                      │
│    → Finds latest file in GCS                      │
│    → Loads data                                     │
│    → Loads trained models                          │
│    → Runs inference                                │
│    → Returns prediction + country contributions    │
└─────────────────────────────────────────────────────┘
```

## Why This Architecture?

### ✓ Separation of Concerns
- **Data pipeline:** Runs once daily (heavy processing)
- **API:** Runs on-demand (fast inference)
- Each can be updated independently

### ✓ Cost Efficient
- Data pipeline: Only runs 5-10 minutes/day
- API: Scales to zero when not in use
- No always-on servers needed

### ✓ Reliability
- If API fails, data pipeline keeps running
- If data pipeline fails, API uses yesterday's data
- Both have independent monitoring

### ✓ Fresh Data
- New data every morning
- API always uses latest available data
- No manual updates needed

## Deployment Checklist

### Step 1: Get Alpha Vantage API Key
- [ ] Sign up at https://www.alphavantage.co/support/#api-key (FREE, 30 seconds)
- [ ] Save your API key

### Step 2: Deploy Data Pipeline
```bash
export GCP_PROJECT_ID="your-project-id"
export ALPHA_VANTAGE_API_KEY="your-api-key"
./deploy_data_pipeline.sh
```
- [ ] Cloud Function deployed
- [ ] Scheduler created (runs daily at 6 AM ET)
- [ ] Test run successful

### Step 3: Deploy Prediction API
```bash
export GCP_PROJECT_ID="your-project-id"
./deploy_cloudrun.sh
```
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] API URL obtained

### Step 4: Test Everything
```bash
# Test data pipeline manually
gcloud functions call oil-gnn-data-pipeline --region=us-central1

# Test prediction API
SERVICE_URL="your-cloud-run-url"
curl -X POST $SERVICE_URL/predict
```
- [ ] Data pipeline creates new file in GCS
- [ ] API returns valid prediction
- [ ] Country contributors included

## Environment Variables Needed

### For Data Pipeline (Cloud Function)
```bash
ALPHA_VANTAGE_API_KEY=your-key          # Required
GCS_BUCKET_NAME=gdelt_raw_3_years       # Your bucket
GCS_PROCESSED_PATH=processed_data/       # Where to save
```

### For Prediction API (Cloud Run)
```bash
GCS_BUCKET_NAME=gdelt_raw_3_years       # Your bucket
GCS_PROCESSED_PATH=processed_data/       # Where data is
GCS_MODELS_PATH=trained_models/          # Where models are
MODEL_RUN_ID=run_20251101_090727_18dd2c # Which model to use
```

## What Happens Daily

### 6:00 AM ET
```
1. Cloud Scheduler publishes message to Pub/Sub
2. Cloud Function triggered
3. Fetches GDELT data for yesterday
4. Fetches oil prices (WTI + Brent)
5. Processes data (same as training pipeline)
6. Engineers features (lags, returns, MAs, RSI, etc.)
7. Saves to GCS: processed_data/final_aligned_data_20251104.json.gz
8. Logs success
```

### Any Time User Requests
```
1. User: POST /predict
2. API lists GCS files in processed_data/
3. API finds latest: final_aligned_data_20251104.json.gz
4. API downloads and parses
5. API loads models (if not cached)
6. API runs prediction
7. API returns JSON with prediction + countries
```

## Monitoring

### Check Data Pipeline
```bash
# View recent runs
gcloud functions logs read oil-gnn-data-pipeline --region=us-central1 --limit=20

# Check scheduler
gcloud scheduler jobs describe oil-gnn-daily-data-job --location=us-central1

# Verify data files
gsutil ls gs://gdelt_raw_3_years/processed_data/ | tail -10
```

### Check Prediction API
```bash
# View API logs
gcloud run services logs read oil-gnn-api --region=us-central1 --limit=20

# Test endpoint
curl -X POST https://your-api-url/predict
```

## Updating

### Update Data Pipeline Code
```bash
# Edit: gnn-backend/app/daily_data_pipeline.py
# Then redeploy:
./deploy_data_pipeline.sh
```

### Update Prediction API
```bash
# Edit: gnn-backend/app/main.py or inference.py
# Then redeploy:
./deploy_cloudrun.sh
```

### Update to New Model
```bash
NEW_MODEL="run_20251104_120000_abc123"

gcloud run services update oil-gnn-api \
  --update-env-vars MODEL_RUN_ID=$NEW_MODEL \
  --region=us-central1
```

## Cost Breakdown

| Component | Cost/Month | Notes |
|-----------|-----------|-------|
| Data Pipeline (Cloud Function) | $0.50-1.00 | Runs 5-10 min/day |
| Scheduler | FREE | First 3 jobs free |
| Prediction API (Cloud Run) | $10-50 | Scales with traffic |
| GCS Storage | $0.03 | ~1.5 GB data |
| Alpha Vantage API | FREE | 25 calls/day limit |
| **Total** | **$10-51/month** | Production-ready |

## Troubleshooting

### Data Pipeline Not Running
```bash
# Check scheduler status
gcloud scheduler jobs describe oil-gnn-daily-data-job --location=us-central1

# Manually trigger
gcloud functions call oil-gnn-data-pipeline --region=us-central1

# View errors
gcloud functions logs read oil-gnn-data-pipeline --region=us-central1 --limit=50
```

### API Using Old Data
```bash
# Check what files exist
gsutil ls -l gs://gdelt_raw_3_years/processed_data/ | tail -5

# Verify data pipeline ran
gcloud functions logs read oil-gnn-data-pipeline --region=us-central1

# Manually run data pipeline
python run_data_pipeline.py
```

### Alpha Vantage Rate Limit
```
Error: API rate limit exceeded
```
**Solution:** Free tier allows 25 calls/day. Pipeline only uses 2/day (WTI + Brent), so this shouldn't happen unless you're running manually many times. Wait 24 hours or upgrade to paid tier ($50/month for unlimited).

## Documentation Reference

- **DATA_PIPELINE.md** - Complete data pipeline documentation
- **QUICKSTART.md** - Quick deployment for prediction API
- **DEPLOYMENT.md** - Full deployment options
- **COMPLETE_GUIDE.md** - Everything about the system
- **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist

## Summary

You now have a **complete, production-ready system** with:

✓ **Automated Data Pipeline**
- Fetches GDELT + oil prices daily
- Processes with same code as training
- Saves to GCS automatically
- Costs ~$1/month

✓ **Prediction API**
- Serves predictions via REST
- Auto-loads latest data
- Scales automatically
- Costs ~$10-50/month

✓ **Zero Manual Work**
- Data updates daily automatically
- API always uses fresh data
- Models cached in memory
- Full monitoring and logging

✓ **Ready for Frontend**
- REST API endpoints
- Country contribution data
- TypeScript integration example
- CORS enabled

**Total deployment time:** 10-15 minutes  
**Total cost:** ~$11-51/month  
**Manual work required:** ZERO (runs itself!)
