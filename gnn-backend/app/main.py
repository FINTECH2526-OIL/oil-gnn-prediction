import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import traceback
import json
import gzip
import requests
import pandas as pd

from .config import config
from .data_loader import DataLoader
from .inference import ModelInference
from prediction_pipeline import HISTORY_WINDOW
from google.cloud import storage

version = f"{sys.version_info.major}.{sys.version_info.minor}"

app = FastAPI(
    title="Oil Price Prediction API",
    description="Hierarchical Temporal-Graph Model for Oil Price Prediction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler for CORS on errors
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Lazy initialization - don't load at startup
data_loader = None
model_inference = None

def get_data_loader():
    global data_loader
    if data_loader is None:
        data_loader = DataLoader()
    return data_loader

def get_model_inference():
    global model_inference
    if model_inference is None:
        model_inference = ModelInference()
    return model_inference

class PredictionResponse(BaseModel):
    date: str
    predicted_delta: float
    predicted_direction: str
    top_contributors: Dict[str, Dict[str, float]]
    total_abs_contribution: float
    num_countries: int
    model_version: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    python_version: str

@app.get("/", response_model=HealthResponse)
async def health_check():
    try:
        model_inf = get_model_inference()
        models_loaded = model_inf.models_loaded
    except Exception as e:
        print(f"Health check model load error: {e}")
        models_loaded = False
    
    return {
        "status": "healthy",
        "model_loaded": models_loaded,
        "python_version": version
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    try:
        model_inf = get_model_inference()
        models_loaded = model_inf.models_loaded
    except:
        models_loaded = False
    
    return {
        "status": "healthy",
        "model_loaded": models_loaded,
        "python_version": version
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict():
    try:
        loader = get_data_loader()
        model_inf = get_model_inference()
        
        model_inf.load_models()
        
        df = loader.get_latest_data()
        
        if model_inf.feature_columns is not None:
            feature_cols = []
            missing_from_df = []
            for col in model_inf.feature_columns:
                if col in df.columns:
                    feature_cols.append(col)
                else:
                    missing_from_df.append(col)
                    df[col] = 0.0
                    feature_cols.append(col)

            if missing_from_df:
                print(f"WARNING: Backfilled {len(missing_from_df)} missing features with zeros: {missing_from_df[:10]}")

            meta_cols = [c for c in ['country', 'date', 'country_iso3'] if c in df.columns]
            df = df[meta_cols + feature_cols]

            expected = getattr(model_inf.scaler_graph, 'n_features_in_', None) or getattr(model_inf.scaler_X, 'n_features_in_', len(feature_cols))
            if len(feature_cols) != expected:
                print(f"WARNING: Feature count {len(feature_cols)} does not match expected {expected}; proceeding with full feature set.")
        else:
            exclude_cols = ['country', 'date']
            feature_cols = [c for c in df.columns 
                           if c not in exclude_cols
                           and 'next' not in c 
                           and 'surprise' not in c
                           and df[c].dtype != 'object']
        
        result = model_inf.get_prediction_with_explanation(df, feature_cols)
        
        predicted_delta = result["predicted_delta"]
        direction = "UP" if predicted_delta > 0 else "DOWN" if predicted_delta < 0 else "FLAT"
        
        return {
            "date": df['date'].max().strftime("%Y-%m-%d"),
            "predicted_delta": predicted_delta,
            "predicted_direction": direction,
            "top_contributors": result["top_contributors"],
            "total_abs_contribution": result["total_abs_contribution"],
            "num_countries": result["num_countries"],
            "model_version": config.MODEL_RUN_ID
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}\n{traceback.format_exc()}")

@app.get("/contributors")
async def get_top_contributors():
    try:
        loader = get_data_loader()
        model_inf = get_model_inference()
        
        df = loader.get_latest_data()
        
        # Exclude country and date columns, plus any target/object columns
        exclude_cols = ['country', 'date']
        feature_cols = [c for c in df.columns 
                       if c not in exclude_cols
                       and 'next' not in c 
                       and 'surprise' not in c
                       and df[c].dtype != 'object']
        
        result = model_inf.get_prediction_with_explanation(df, feature_cols)
        
        contributors_list = []
        for country, data in result["top_contributors"].items():
            contributors_list.append({
                "country": country,
                "contribution": data["contribution"],
                "percentage": data["percentage"],
                "raw_prediction": data["raw_prediction"],
                "attention_weight": data["attention_weight"]
            })
        
        return {
            "date": df['date'].max().strftime("%Y-%m-%d"),
            "contributors": contributors_list,
            "total_abs_contribution": result["total_abs_contribution"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contributors: {str(e)}")


@app.get("/history")
async def get_prediction_history(
    days: int = Query(30, ge=1, le=HISTORY_WINDOW),
    start_date: Optional[str] = None,
):
    """
    Fetch prediction history from GCS bucket.
    Returns up to 120 days of predictions with actuals when available.
    """
    try:
        client = storage.Client()
        bucket = client.bucket(config.GCS_BUCKET_NAME)
        history_blob_path = f"{config.GCS_PROCESSED_PATH}predictions/history.json"
        
        blob = bucket.blob(history_blob_path)
        
        if not blob.exists():
            return []
        
        content = blob.download_as_text()
        history = json.loads(content)
        
        # Ensure it's a list
        if isinstance(history, dict) and "records" in history:
            history = history["records"]
        
        if not isinstance(history, list):
            return []
        
        # Sort by feature_date descending (most recent first)
        history_sorted = sorted(
            history,
            key=lambda r: r.get("feature_date", ""),
            reverse=True,
        )

        filtered_history = history_sorted

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                filtered_history = [
                    item
                    for item in filtered_history
                    if item.get("feature_date")
                    and datetime.strptime(item["feature_date"], "%Y-%m-%d").date() >= start_dt
                ]
            except ValueError:
                pass

        return filtered_history[:days]
    
    except Exception as e:
        # Return empty list if file doesn't exist yet or any error
        print(f"Error fetching history: {e}")
        return []

@app.post("/update")
async def update_predictions(force_refresh: bool = False):
    """
    Quick update: Start data pipeline asynchronously.
    Returns immediately with status. Pipeline runs in background.
    """
    try:
        import subprocess
        from datetime import date
        import os
        
        today = date.today()
        print(f"[UPDATE] Today is {today}, starting async update...")
        
        # Get API key from environment
        alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not alpha_key:
            raise HTTPException(
                status_code=500,
                detail="ALPHA_VANTAGE_API_KEY not configured"
            )
        
        # Quick check of Alpha Vantage (10 second timeout)
        response = requests.get(
            f"https://www.alphavantage.co/query?function=WTI&interval=daily&apikey={alpha_key}",
            timeout=10
        )
        av_data = response.json()
        
        if "data" not in av_data or not av_data["data"]:
            return {
                "status": "no_new_data",
                "message": "Alpha Vantage returned no data",
                "latest_alpha_vantage_date": None
            }
        
        # Get latest valid date
        latest_av_date = None
        for item in av_data["data"]:
            try:
                if item.get("value") and item["value"] != ".":
                    latest_av_date = item["date"]
                    break
            except:
                continue
        
        if not latest_av_date:
            return {
                "status": "no_new_data",
                "message": "No valid oil price data in Alpha Vantage",
                "latest_alpha_vantage_date": None
            }
        
        print(f"[UPDATE] Latest Alpha Vantage date: {latest_av_date}")
        
        # Check our latest processed data
        client = storage.Client()
        bucket = client.bucket(config.GCS_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix='processed_data/final_aligned_data_'))
        if not blobs:
            latest_processed_date = None
        else:
            latest_blob = max(blobs, key=lambda b: b.name)
            date_str = latest_blob.name.split('_')[-1].replace('.json.gz', '')
            latest_processed_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        print(f"[UPDATE] Latest processed data date: {latest_processed_date}")
        
        needs_update = force_refresh or (latest_processed_date is None) or (latest_av_date > latest_processed_date)
        
        if not needs_update:
            # Just run quick forecast (non-blocking, ~5 seconds)
            print("[UPDATE] Running quick forecast...")
            subprocess.Popen(
                ["python", "/workspace/multi_step_forecast.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return {
                "status": "forecast_started",
                "message": "Forecast generation started. Refresh in 10 seconds.",
                "latest_alpha_vantage_date": latest_av_date,
                "latest_processed_date": latest_processed_date
            }
        
        # Start pipeline in background (non-blocking)
        print(f"[UPDATE] Starting pipeline for {latest_av_date} in background...")
        subprocess.Popen(
            ["python", "/workspace/run_data_pipeline.py", "--date", latest_av_date],
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL
        )
        
        return {
            "status": "update_started",
            "message": f"Data pipeline started for {latest_av_date}. This will take 5-10 minutes. Refresh page later.",
            "latest_alpha_vantage_date": latest_av_date,
            "previous_processed_date": latest_processed_date,
            "estimated_completion": "5-10 minutes"
        }
    
    except Exception as e:
        import traceback
        print(f"[UPDATE] Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")


class PriceEntry(BaseModel):
    date: str           # YYYY-MM-DD
    wti_price: float
    brent_price: float

class ManualPatchRequest(BaseModel):
    prices: List[PriceEntry]

@app.post("/admin/patch-prices")
async def admin_patch_prices(request: ManualPatchRequest):
    """
    Manually inject oil price rows for dates not yet available from Alpha Vantage.
    Downloads latest GCS aligned data, patches in the supplied prices,
    re-engineers all rolling features, uploads back to GCS as today's dataset,
    then runs prediction and returns the result.
    """
    try:
        loader = get_data_loader()
        model_inf = get_model_inference()

        # 1. Find and download latest aligned data from GCS
        client = storage.Client()
        bucket = client.bucket(config.GCS_BUCKET_NAME)
        blobs = list(client.list_blobs(config.GCS_BUCKET_NAME, prefix=config.GCS_PROCESSED_PATH))
        aligned_blobs = sorted(
            [b for b in blobs if "final_aligned_data_" in b.name and b.name.endswith(".json.gz")],
            key=lambda b: b.name, reverse=True
        )
        if not aligned_blobs:
            raise HTTPException(status_code=500, detail="No final_aligned_data_*.json.gz found in GCS")

        raw_bytes = aligned_blobs[0].download_as_bytes()
        raw_json = gzip.decompress(raw_bytes).decode("utf-8")
        df = pd.DataFrame.from_records(json.loads(raw_json))
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["country_iso3", "date"]).reset_index(drop=True)
        print(f"[ADMIN] Loaded {len(df)} rows from {aligned_blobs[0].name}, up to {df['date'].max().date()}")

        # 2. Build manual prices map
        manual_prices = {
            pd.Timestamp(e.date): {"wti_price": e.wti_price, "brent_price": e.brent_price}
            for e in request.prices
        }

        # 3. Inject / update rows per country
        dates_in_data = set(df["date"].unique())
        new_rows = []
        for country in df["country_iso3"].unique():
            country_df = df[df["country_iso3"] == country].sort_values("date")
            last_row = country_df.iloc[-1].to_dict()
            for new_date, prices in sorted(manual_prices.items()):
                if new_date in dates_in_data:
                    mask = (df["country_iso3"] == country) & (df["date"] == new_date)
                    if mask.any():
                        df.loc[mask, "wti_price"] = prices["wti_price"]
                        df.loc[mask, "brent_price"] = prices["brent_price"]
                else:
                    row = last_row.copy()
                    row["date"] = new_date
                    row["wti_price"] = prices["wti_price"]
                    row["brent_price"] = prices["brent_price"]
                    new_rows.append(row)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            new_df["date"] = pd.to_datetime(new_df["date"])
            df = pd.concat([df, new_df], ignore_index=True)

        df = df.sort_values(["country_iso3", "date"]).reset_index(drop=True)
        print(f"[ADMIN] After injection: {len(df)} rows, up to {df['date'].max().date()}")

        # 4. Re-engineer all rolling features
        df = loader.engineer_features(df)
        df = df.fillna(0)

        # 5. Upload to GCS as today's aligned data file
        today_str = datetime.now().strftime("%Y%m%d")
        output_path = f"{config.GCS_PROCESSED_PATH}final_aligned_data_{today_str}.json.gz"
        records_out = df.to_dict("records")
        json_bytes = json.dumps(records_out, ensure_ascii=False, default=str).encode("utf-8")
        blob_out = bucket.blob(output_path)
        blob_out.upload_from_string(gzip.compress(json_bytes), content_type="application/gzip")
        print(f"[ADMIN] Uploaded {output_path}")

        # 6. Re-load from GCS so inference uses the fresh file
        df_fresh = loader.get_latest_data()

        # 7. Run prediction (same logic as /predict)
        model_inf.load_models()
        if model_inf.feature_columns is not None:
            feature_cols = []
            for col in model_inf.feature_columns:
                if col not in df_fresh.columns:
                    df_fresh[col] = 0.0
                feature_cols.append(col)
        else:
            exclude_cols = ["country", "date"]
            feature_cols = [c for c in df_fresh.columns
                            if c not in exclude_cols
                            and "next" not in c
                            and "surprise" not in c
                            and df_fresh[c].dtype != "object"]

        result = model_inf.get_prediction_with_explanation(df_fresh, feature_cols)
        predicted_delta = result["predicted_delta"]
        direction = "UP" if predicted_delta > 0 else "DOWN" if predicted_delta < 0 else "FLAT"

        latest_date = df_fresh["date"].max()
        latest_rows = df_fresh[df_fresh["date"] == latest_date]
        reference_wti = float(latest_rows["wti_price"].iloc[0]) if not latest_rows.empty else None

        # 8. Calculate next business day for prediction_for_date
        next_day = latest_date + timedelta(days=1)
        while next_day.weekday() >= 5:  # 5=Sat, 6=Sun
            next_day += timedelta(days=1)
        prediction_for_date = next_day.strftime("%Y-%m-%d")

        predicted_close = (reference_wti or 0) + predicted_delta

        # Convert top_contributors dict to list format for history
        contributors_list = [
            {"country": country, **info}
            for country, info in result["top_contributors"].items()
        ]

        # 9. Save to prediction history
        try:
            new_record = {
                "feature_date": latest_date.strftime("%Y-%m-%d"),
                "prediction_for_date": prediction_for_date,
                "reference_close": reference_wti,
                "predicted_delta": predicted_delta,
                "predicted_close": predicted_close,
                "total_abs_contribution": result["total_abs_contribution"],
                "num_countries": result["num_countries"],
                "model_version": config.MODEL_RUN_ID,
                "top_contributors": contributors_list,
                "actual_close": None,
                "error_delta": None,
            }

            next_day2 = next_day + timedelta(days=1)
            while next_day2.weekday() >= 5:
                next_day2 += timedelta(days=1)
            chained_record = {
                "feature_date": next_day.strftime("%Y-%m-%d"),
                "prediction_for_date": next_day2.strftime("%Y-%m-%d"),
                "reference_close": predicted_close,
                "predicted_delta": predicted_delta,
                "predicted_close": predicted_close + predicted_delta,
                "total_abs_contribution": result["total_abs_contribution"],
                "num_countries": result["num_countries"],
                "model_version": config.MODEL_RUN_ID,
                "top_contributors": contributors_list,
                "actual_close": None,
                "error_delta": None,
            }

            history_blob_path = f"{config.GCS_PROCESSED_PATH}predictions/history.json"
            history_blob = bucket.blob(history_blob_path)
            if history_blob.exists():
                existing = json.loads(history_blob.download_as_text())
                if isinstance(existing, dict) and "records" in existing:
                    existing = existing["records"]
            else:
                existing = []
            skip = {new_record["feature_date"], chained_record["feature_date"]}
            existing = [r for r in existing if r.get("feature_date") not in skip]
            existing.insert(0, chained_record)
            existing.insert(0, new_record)
            history_blob.upload_from_string(json.dumps(existing), content_type="application/json")
            print(f"[ADMIN] Saved prediction to history: {new_record['feature_date']} -> {prediction_for_date}")
            print(f"[ADMIN] Saved chained prediction: {chained_record['feature_date']} -> {chained_record['prediction_for_date']}")
        except Exception as hist_err:
            print(f"[ADMIN] Warning: failed to save to history: {hist_err}")

        return {
            "date": latest_date.strftime("%Y-%m-%d"),
            "predicted_delta": predicted_delta,
            "predicted_direction": direction,
            "top_contributors": result["top_contributors"],
            "total_abs_contribution": result["total_abs_contribution"],
            "num_countries": result["num_countries"],
            "model_version": config.MODEL_RUN_ID,
            "reference_wti": reference_wti,
            "injected_dates": [str(d.date()) for d in sorted(manual_prices.keys())],
            "gcs_file": output_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch failed: {str(e)}\n{traceback.format_exc()}")


@app.post("/backfill")
async def backfill_history(days: int = 30, start_date: Optional[str] = None, dry_run: bool = False):
    """
    Backfill prediction history for the last N days.
    This generates historical predictions and stores them in GCS.
    """
    try:
        import subprocess
        import json
        
        # Run the backfill script
        command = ["python", "/workspace/backfill_predictions.py", "--days", str(days)]
        if start_date:
            command.extend(["--start-date", start_date])
        if dry_run:
            command.append("--dry-run")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Backfill failed: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Backfill timeout after 5 minutes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backfill error: {str(e)}")


