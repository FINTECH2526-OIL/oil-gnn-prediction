# How to Regenerate GCS Data

## The Problem
The current GCS data file was created BEFORE we added `tone_std` and theme columns to the data pipeline.
The deployed API now has a FAILSAFE that uses default values (0) for missing columns, but for accurate predictions, you should regenerate the data.

## Solution: Run the Data Pipeline

### Option 1: Run from Cloud Run (Recommended)
```bash
# Trigger the data pipeline through the API
curl -X POST https://oil-gnn-api-1072886277511.us-central1.run.app/run-pipeline \
  -H "Content-Type: application/json"
```

### Option 2: Run Locally
```bash
# Set environment variables
export GCS_BUCKET_NAME="oil-gnn-data-bucket"
export GCP_PROJECT_ID="manifest-vault-470110-k5"
export ALPHA_VANTAGE_API_KEY="WY4DN5PO5LQ3INPJ"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

# Run the pipeline for yesterday
python run_data_pipeline.py

# Or run for a specific date
python run_data_pipeline.py --date 2024-11-12

# Or run with more historical data
python run_data_pipeline.py --date 2024-11-12 --days-back 60
```

### Option 3: Deploy a Cloud Function/Cloud Run Job
See `deploy_data_pipeline.sh` for automated deployment.

## What the Pipeline Does
1. Fetches oil prices from Alpha Vantage (WTI and Brent)
2. Fetches GDELT news data for the past 30 days
3. Processes GDELT data to extract:
   - Sentiment metrics (avg_tone → avg_sentiment, tone_std)
   - Event counts
   - Theme counts per country (energy, conflict, sanctions, trade, economy, policy)
4. Aligns oil prices with news data by date and country
5. Saves to GCS: `gs://oil-gnn-data-bucket/processed/final_aligned_data_YYYYMMDD.json.gz`

## Verify the New Data
After running the pipeline, check the GCS bucket:
```bash
gsutil ls -lh gs://oil-gnn-data-bucket/processed/

# Download and inspect the latest file
gsutil cat gs://oil-gnn-data-bucket/processed/final_aligned_data_20241112.json.gz | gunzip | jq '.[0]'
```

Expected columns in the output:
- date, country, country_iso3
- wti_price, brent_price
- avg_sentiment, tone_std, event_count
- theme_energy, theme_conflict, theme_sanctions, theme_trade, theme_economy, theme_policy
- Plus all engineered features (lags, MAs, etc.)

## Current Failsafe
Until you regenerate the data, the API uses these defaults:
- `tone_std`: 0.0
- `event_count`: 0
- `avg_sentiment`: 0.0
- All themes: 0

This allows the API to work, but predictions will be less accurate without real news sentiment data.
