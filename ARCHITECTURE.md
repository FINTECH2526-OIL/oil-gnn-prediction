# Architecture Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DAILY DATA PIPELINE                          │
│                                                                       │
│  ┌──────────────┐        ┌──────────────┐       ┌─────────────┐    │
│  │   Cloud      │ 6AM ET │   Cloud      │       │   GDELT     │    │
│  │  Scheduler   ├───────→│  Function    ├──────→│   API       │    │
│  │              │        │              │       │             │    │
│  └──────────────┘        │  - Fetch     │       └─────────────┘    │
│                          │  - Process   │                           │
│                          │  - Engineer  │       ┌─────────────┐    │
│                          │  - Save      ├──────→│    Alpha    │    │
│                          │              │       │  Vantage    │    │
│                          └──────┬───────┘       │   (Oil $)   │    │
│                                 │               └─────────────┘    │
│                                 ↓                                   │
│                       ┌──────────────────┐                          │
│                       │   GCS Bucket     │                          │
│                       │  processed_data/ │                          │
│                       │  ├── final_...gz │                          │
│                       └──────────────────┘                          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Latest data
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         PREDICTION API                               │
│                                                                       │
│  ┌──────────────┐        ┌──────────────┐       ┌─────────────┐    │
│  │   Frontend   │        │  Cloud Run   │       │ GCS Bucket  │    │
│  │   / User     ├───────→│   FastAPI    ├──────→│   Models    │    │
│  │              │  POST  │              │       │  artifacts/ │    │
│  └──────────────┘ /predict│  - Load data│       └─────────────┘    │
│                          │  - Load model│                           │
│        ┌─────────────────┤  - Predict   │                           │
│        │ JSON Response   │  - Explain   │                           │
│        │ {               │              │                           │
│        │   "predicted_   └──────────────┘                           │
│        │    delta": 0.25,                                           │
│        │   "top_         ┌──────────────────────┐                  │
│        │    contributors":│ Response Format      │                  │
│        │    {...}        │ ├── predicted_delta  │                  │
│        │ }               │ ├── direction        │                  │
│        └────────────────→│ ├── top_contributors │                  │
│                          │ └── country %'s      │                  │
│                          └──────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘

```

## Data Flow Timeline

```
Day N-1 (e.g., Nov 3)
23:59 ─────────────────────────────────────────────────────────
                Oil markets close at 17:00 ET
                GDELT continues collecting news
00:00 ─────────────────────────────────────────────────────────

Day N (e.g., Nov 4)
00:00 ─────────────────────────────────────────────────────────
        ↓
        ↓ (GDELT collecting data for Nov 3)
        ↓
06:00 ─┬─ CLOUD SCHEDULER TRIGGERS ──────────────────────────
       │
       ├─→ Cloud Function starts
       │   └─→ Fetch GDELT data for Nov 3 (all 96 15-min files)
       │   └─→ Fetch oil prices (WTI + Brent)
       │   └─→ Process & engineer features
       │   └─→ Save: final_aligned_data_20251103.json.gz
       │
06:10 ─┴─ DATA PIPELINE COMPLETE ────────────────────────────
       │
       │ (Fresh data now available in GCS)
       │
06:15 ─┬─ USER REQUESTS PREDICTION ───────────────────────────
       │
       ├─→ POST /predict
       │   └─→ API finds: final_aligned_data_20251103.json.gz
       │   └─→ Loads data
       │   └─→ Loads model
       │   └─→ Runs inference
       │   └─→ Returns prediction
       │
06:16 ─┴─ PREDICTION RETURNED ────────────────────────────────

```

## Component Details

### Data Pipeline (Cloud Function)

```
Input:
  - Date: Yesterday (auto)
  - GDELT: 96 files × 15-min intervals
  - Oil $: 90 days history

Process:
  1. Extract countries from locations
  2. Calculate tone metrics
  3. Aggregate themes
  4. Align with oil prices
  5. Engineer features:
     ├── Price lags (1,2,7 days)
     ├── Returns & deltas
     ├── Moving averages (5,10,20,30)
     ├── Momentum indicators
     ├── RSI calculations
     └── News metrics

Output:
  - GCS: final_aligned_data_YYYYMMDD.json.gz
  - Format: Country-date-features
  - Size: ~50 MB compressed

Runs: Daily at 6 AM ET
Cost: ~$1/month
```

### Prediction API (Cloud Run)

```
Input:
  - POST /predict (no body needed)

Process:
  1. List GCS files
  2. Find latest data file
  3. Download & decompress
  4. Load trained models (cached)
  5. Run prediction per country
  6. Compute attention weights
  7. Aggregate final prediction

Output:
  {
    "predicted_delta": 0.25,
    "predicted_direction": "UP",
    "top_contributors": {
      "SAU": {
        "contribution": 0.178,
        "percentage": 29.6,
        ...
      }
    }
  }

Runs: On-demand
Cost: ~$10-50/month
```

## File Locations in GCS

```
gs://gdelt_raw_3_years/
│
├── processed_data/              ← Daily pipeline output
│   ├── final_aligned_data_20251101.json.gz
│   ├── final_aligned_data_20251102.json.gz
│   ├── final_aligned_data_20251103.json.gz
│   └── final_aligned_data_20251104.json.gz  ← Latest (API uses this)
│
└── trained_models/              ← Training output
    └── run_20251101_090727_18dd2c/
        └── artifacts/
            ├── model_base.pkl
            ├── model_enhanced.pkl
            ├── country_models.obj
            ├── scaler_X.pkl
            ├── adjacency.npy
            └── metadata.json
```

## Deployment Flow

```
Step 1: Deploy Data Pipeline
───────────────────────────────
$ export ALPHA_VANTAGE_API_KEY="..."
$ ./deploy_data_pipeline.sh
  ↓
  Creates:
  ├── Cloud Function: oil-gnn-data-pipeline
  ├── Pub/Sub Topic: oil-gnn-daily-trigger
  └── Scheduler Job: oil-gnn-daily-data-job
  
  Result: Runs daily at 6 AM ET ✓

Step 2: Deploy Prediction API
───────────────────────────────
$ ./deploy_cloudrun.sh
  ↓
  Creates:
  ├── Docker Image → Artifact Registry
  └── Cloud Run Service: oil-gnn-api
  
  Result: API live at https://...run.app ✓

Step 3: Test
───────────────────────────────
$ curl -X POST https://...run.app/predict
  ↓
  Returns: Prediction + Countries ✓
```

## Monitoring Dashboard

```
Data Pipeline Health
────────────────────────────────
Last Run:        2025-11-04 06:05 AM ✓
Status:          Success
Duration:        8 minutes
Output:          final_aligned_data_20251103.json.gz
Records:         1,247 countries × features
Next Run:        2025-11-05 06:00 AM

Prediction API Health
────────────────────────────────
Status:          Running ✓
Requests (24h):  127
Avg Response:    2.3 seconds
Success Rate:    99.2%
Latest Data:     2025-11-03 (yesterday)
Model Version:   run_20251101_090727_18dd2c
```

## Error Handling

```
Data Pipeline Failures
────────────────────────────────
GDELT unavailable  → Skip file, continue
                     (Logs warning)

Oil API limit      → Use cached prices
                     (Logs warning)

Processing error   → Save partial data
                     (Logs error, continues)

GCS write fails    → Retry 3 times
                     (Fails job if all fail)

Prediction API Failures
────────────────────────────────
No data in GCS     → Return 503 with message
                     "Data pipeline pending"

Model load error   → Return 500 with details
                     (Admin notified)

Invalid data       → Return 400 with validation
                     (Logs for debugging)

Timeout            → 300s limit, then 503
                     (Rare, only on cold start)
```

