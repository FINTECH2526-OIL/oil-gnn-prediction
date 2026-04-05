# oil-gnn-prediction

Predicts short-term WTI crude oil price movements using a Hierarchical Temporal Graph Neural Network combined with Gradient Boosted Trees. The model ingests multi-country macroeconomic and energy features, runs GNN-based attribution across 72 countries, and outputs a predicted price delta for the next trading day.

---

## Architecture

```
gnn-backend/     FastAPI inference server (Cloud Run)
gnn-frontend/    React + Vite dashboard (Cloud Run)
deployment/      Cloud Build and infrastructure configs
```

### Backend

- `/predict` -- runs the GNN model on the latest aligned data from GCS and returns a predicted price delta
- `/history` -- returns prediction history with actuals from GCS (`processed_data/predictions/history.json`)
- `/admin/patch-prices` -- accepts manual WTI/Brent price entries, patches the aligned dataset, re-engineers features, runs prediction, and saves both the primary and a forward-chained prediction to history
- `/update` -- triggers the data pipeline or forecast script in the background

### Frontend

```
gnn-frontend/src/
  components/layout/    navbar, sidebar, layout shell
  pages/                Dashboard, GraphView, AdminPage
  services/             API client (api.ts)
  store/                Zustand state
  types/                TypeScript types
```

Routes:
- `/dashboard` -- price prediction chart, metrics, top contributor table
- `/graph` -- Cytoscape.js network graph of country contributions with date slider
- `/manualinputforoilprice` -- standalone admin page for manual price input (not linked from main UI)

---

## Data Flow

1. Alpha Vantage (WTI/Brent daily prices) + macroeconomic feeds are ingested by the pipeline
2. Features are aligned per country and stored as `processed_data/final_aligned_data_YYYYMMDD.json.gz` in GCS
3. The GNN model runs on the latest aligned file and writes a prediction record to `processed_data/predictions/history.json`
4. The frontend fetches history via `/history` and renders the chart

When manual prices are submitted via the admin page, the backend patches the GCS dataset, re-engineers rolling features, and immediately runs and saves a new prediction.

---

## Prediction Display

The model's output date is offset by one day relative to the input feature date. The frontend corrects for this at display time:

- Dashboard chart: each date label shows the predicted value from the following record, and the furthest-ahead date is hidden
- Graph network page: prediction date labels are shifted back by one calendar day
- The admin endpoint saves two records per run -- the primary prediction and a forward-chained record using the predicted price as the next reference -- so that the current day and the next trading day are always visible in the UI

---

## Deployment

Frontend build:

```
gcloud builds submit --config cloudbuild-frontend.yaml --project=oilhaidilao
```

Backend build:

```
gcloud builds submit --config cloudbuild.yaml --project=oilhaidilao
```

Services:
- Frontend: `https://oil-gnn-frontend-1024808897469.us-central1.run.app`
- Backend: `https://oil-gnn-backend-1024808897469.us-central1.run.app`
- GCP project: `oilhaidilao`

---

## Graph Visualisation

Cytoscape.js renders the contributor network. Node size represents impact percentage, edge width represents contribution strength, and colour indicates direction (green = positive, red = negative). The date slider steps through the prediction history.
