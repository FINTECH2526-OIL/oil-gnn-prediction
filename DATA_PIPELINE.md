# Daily Data Pipeline Documentation

## Overview

The daily data pipeline automatically fetches, processes, and aligns new data every day for your oil price prediction model. It runs the same data engineering and feature creation as your training code.

## What It Does

Every day at 6:00 AM ET (after oil markets close), the pipeline:

1. **Fetches GDELT News Data** - Downloads the previous day's global news events
2. **Fetches Oil Prices** - Gets latest WTI and Brent prices from Alpha Vantage
3. **Processes & Aligns** - Applies the same transformations as your training code:
   - Extracts country mentions from news
   - Calculates tone metrics
   - Aggregates theme counts
   - Aligns with oil price data
4. **Engineers Features** - Creates all the same features:
   - Price lags (1, 2, 7 days)
   - Returns and deltas
   - Moving averages (5, 10, 20, 30 day windows)
   - Momentum indicators
   - RSI calculations
   - Article count changes
   - Tone changes
5. **Saves to GCS** - Uploads processed data to your bucket

## Architecture

```
┌─────────────────┐
│  Cloud Scheduler │  (Triggers daily at 6 AM ET)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cloud Function   │  (Runs data pipeline)
│  - Fetch GDELT   │
│  - Fetch Oil $   │
│  - Process       │
│  - Feature Eng   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GCS Bucket     │  (Stores processed data)
│  processed_data/ │
│  ├── final_aligned_data_20251104.json.gz
│  ├── final_aligned_data_20251103.json.gz
│  └── ...
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Cloud Run API   │  (Uses latest data for predictions)
│  /predict        │
└─────────────────┘
```

## Deployment

### Prerequisites

1. **Alpha Vantage API Key** (FREE)
   - Get it here: https://www.alphavantage.co/support/#api-key
   - Takes 30 seconds to sign up
   - Free tier: 25 API calls per day (more than enough)

2. **GCP Project Setup**
   ```bash
   # Enable required APIs
   gcloud services enable \
     cloudfunctions.googleapis.com \
     cloudscheduler.googleapis.com \
     pubsub.googleapis.com
   ```

### Deploy the Pipeline

```bash
# Set your Alpha Vantage API key
export ALPHA_VANTAGE_API_KEY="your-api-key-here"

# Set GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export GCS_BUCKET_NAME="gdelt_raw_3_years"

# Deploy the Cloud Function and Scheduler
./deploy_data_pipeline.sh
```

That's it! The pipeline will now run automatically every day.

## Schedule

- **Trigger Time:** 6:00 AM Eastern Time (11:00 AM UTC)
- **Frequency:** Daily
- **Why 6 AM ET?** Oil markets close at 5:00 PM ET, so we fetch the previous day's complete data

## Manual Execution

### Test Locally

```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export ALPHA_VANTAGE_API_KEY="your-api-key"
export GCS_BUCKET_NAME="gdelt_raw_3_years"

# Run for yesterday
python run_data_pipeline.py

# Run for specific date
python run_data_pipeline.py --date 2025-11-04
```

### Trigger Cloud Function Manually

```bash
# Trigger for yesterday
gcloud functions call oil-gnn-data-pipeline \
  --region=us-central1

# Trigger for specific date
gcloud functions call oil-gnn-data-pipeline \
  --region=us-central1 \
  --data='{"date":"2025-11-04"}'
```

## Data Flow Details

### 1. GDELT Data Fetching

```python
# Fetches all 15-minute files for the target date
# Format: YYYYMMDDHHMMSS.gkg.csv.zip
# Example URLs:
#   http://data.gdeltproject.org/gdeltv2/20251104000000.gkg.csv.zip
#   http://data.gdeltproject.org/gdeltv2/20251104001500.gkg.csv.zip
#   ... (96 files per day, every 15 minutes)
```

**Extracted Fields:**
- Country mentions (from V21LOCATIONS)
- Tone metrics (from V21TONE)
- Themes (from V21THEMES)
- Article metadata

### 2. Oil Price Fetching

```python
# Alpha Vantage WTI endpoint
GET https://www.alphavantage.co/query?function=WTI&interval=daily

# Alpha Vantage Brent endpoint
GET https://www.alphavantage.co/query?function=BRENT&interval=daily
```

**Retrieved:** Last 90 days of prices (for lag features)

### 3. Feature Engineering

**Same as Training Code:**

```python
# Price features
- wti_price, brent_price
- wti_price_lag1, lag2, lag7
- wti_return (pct_change)
- wti_delta (diff)

# Moving averages
- wti_return_ma5, ma10, ma20, ma30
- wti_return_std5, std10, std20, std30

# Technical indicators
- wti_momentum_5_20 (ma5 - ma20)
- wti_rsi (14-period RSI)

# News features (per country)
- article_count
- article_count_lag1
- article_count_change
- avg_tone
- tone_lag1
- tone_change
```

### 4. Output Format

```json
{
  "date": "2025-11-04",
  "country": "SAU",
  "country_iso3": "SAU",
  "wti_price": 73.25,
  "brent_price": 77.10,
  "wti_price_lag1": 72.80,
  "wti_return": 0.00618,
  "wti_delta": 0.45,
  "wti_return_ma5": 0.00523,
  "wti_rsi": 58.4,
  "article_count": 142,
  "article_count_change": 0.12,
  "avg_tone": -2.34,
  "tone_change": -0.15
}
```

File saved as: `processed_data/final_aligned_data_20251104.json.gz`

## Integration with Inference API

The inference API (`gnn-backend/app/data_loader.py`) automatically:
1. Lists all files in `processed_data/`
2. Finds the most recent `final_aligned_data_*.json.gz`
3. Downloads and uses it for predictions

**No code changes needed!** The API will automatically use the latest data.

## Monitoring

### View Cloud Function Logs

```bash
# Recent logs
gcloud functions logs read oil-gnn-data-pipeline \
  --region=us-central1 \
  --limit=50

# Follow logs in real-time
gcloud functions logs read oil-gnn-data-pipeline \
  --region=us-central1 \
  --limit=50 \
  --follow
```

### Check Scheduler Status

```bash
# List jobs
gcloud scheduler jobs list --location=us-central1

# View specific job
gcloud scheduler jobs describe oil-gnn-daily-data-job \
  --location=us-central1
```

### Verify Data Files

```bash
# List recent data files
gsutil ls -l gs://gdelt_raw_3_years/processed_data/ | tail -10

# Check latest file
gsutil ls -l gs://gdelt_raw_3_years/processed_data/ | grep final_aligned | tail -1
```

## Error Handling

The pipeline includes robust error handling:

- **GDELT file missing:** Skips and continues with other files
- **Alpha Vantage rate limit:** Returns cached data with warning
- **Network issues:** Retries with exponential backoff
- **Data quality issues:** Logs warnings but completes processing
- **Feature calculation errors:** Fills with safe defaults

### Common Issues

**1. Alpha Vantage API Limit**
```
Error: API rate limit exceeded
```
**Solution:** Free tier allows 25 calls/day. If you hit the limit, the pipeline uses the last cached oil prices.

**2. GDELT Data Gaps**
```
Warning: No GDELT data for 2025-11-04
```
**Solution:** This is normal for recent dates. GDELT has a ~2-3 hour delay. The pipeline will succeed with partial data.

**3. Missing Features**
```
Warning: wti_price_lag7 has NaN values
```
**Solution:** First 7 days won't have 7-day lags. Pipeline fills with 0 or forward-fill.

## Cost Estimate

### Cloud Function
- **Invocations:** 1/day = 30/month (FREE tier: 2M/month)
- **Compute:** ~5-10 minutes @ 2GB = ~10-20 GB-seconds/day
- **Cost:** ~$0.50-1.00/month

### Cloud Scheduler
- **Jobs:** 1 job, 30 triggers/month
- **Cost:** FREE (First 3 jobs are free)

### GCS Storage
- **Data:** ~50 MB/day compressed = ~1.5 GB/month
- **Cost:** ~$0.03/month

### Alpha Vantage API
- **Calls:** 2/day (WTI + Brent)
- **Cost:** FREE (25 calls/day limit)

**Total: ~$0.50-1.00/month**

## Updating the Pipeline

### Change Schedule

```bash
# Update to run at different time (e.g., 8 AM ET)
gcloud scheduler jobs update pubsub oil-gnn-daily-data-job \
  --location=us-central1 \
  --schedule="0 8 * * *" \
  --time-zone="America/New_York"
```

### Change Data Retention

```bash
# Delete data older than 90 days (lifecycle rule)
gsutil lifecycle set lifecycle.json gs://gdelt_raw_3_years

# lifecycle.json:
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {
      "age": 90,
      "matchesPrefix": ["processed_data/final_aligned_"]
    }
  }]
}
```

### Update Pipeline Code

```bash
# Make changes to daily_data_pipeline.py
# Then redeploy
./deploy_data_pipeline.sh
```

## Testing

### Test Data Fetching

```python
from gnn_backend.app.daily_data_pipeline import DailyDataPipeline
from datetime import datetime

pipeline = DailyDataPipeline()

# Test GDELT fetch
gdelt_df = pipeline.fetch_gdelt_for_date(datetime(2025, 11, 4))
print(f"Fetched {len(gdelt_df)} GDELT records")

# Test oil price fetch
oil_df = pipeline.fetch_oil_prices(days_back=10)
print(f"Fetched {len(oil_df)} days of oil prices")
```

### Test Full Pipeline

```bash
# Dry run (doesn't save to GCS)
python -c "
from gnn_backend.app.daily_data_pipeline import DailyDataPipeline
from datetime import datetime

pipeline = DailyDataPipeline()
result = pipeline.run_daily_update(datetime(2025, 11, 4))
print(f'Success: {result}')
"
```

## Backfilling Historical Data

Need to fill in missing dates?

```bash
# Backfill last 7 days
for i in {1..7}; do
  DATE=$(date -v-${i}d +%Y-%m-%d)  # macOS
  # DATE=$(date -d "${i} days ago" +%Y-%m-%d)  # Linux
  
  echo "Backfilling $DATE..."
  python run_data_pipeline.py --date $DATE
  sleep 60  # Respect Alpha Vantage rate limits
done
```

## Security

-  API keys stored in environment variables (not in code)
-  Cloud Function uses service account (minimal permissions needed)
-  Data stored in private GCS bucket
-  No public endpoints (Scheduler triggers internally)

## Summary

You now have a **fully automated daily data pipeline** that:
-  Runs automatically every day at 6 AM ET
-  Fetches fresh GDELT news + oil prices
-  Applies the same feature engineering as training
-  Saves processed data to GCS
-  Integrates seamlessly with your inference API
-  Costs ~$1/month to run
-  Requires no manual intervention

**Your inference API will always have fresh data!**
