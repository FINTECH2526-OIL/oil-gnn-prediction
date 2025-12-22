import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
import traceback
import json
import gzip
import requests

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
    except:
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

            expected = getattr(model_inf.scaler_X, 'n_features_in_', len(feature_cols))
            if len(feature_cols) != expected:
                raise ValueError(
                    f"Feature mismatch after alignment: scaler expects {expected}, prepared {len(feature_cols)}."
                )
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
    try:
        import subprocess
        from datetime import date
        import requests
        import os
        
        today = date.today()
        print(f"[UPDATE] Today is {today}, checking for new data...")
        
        # Get API key from environment
        alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not alpha_key:
            raise HTTPException(
                status_code=500,
                detail="ALPHA_VANTAGE_API_KEY not configured"
            )
        
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
            print("[UPDATE] No new data, running multi-step forecast only...")
            result = subprocess.run(
                ["python", "/workspace/multi_step_forecast.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    "status": "forecast_updated",
                    "message": "Extended predictions using existing data",
                    "latest_alpha_vantage_date": latest_av_date,
                    "latest_processed_date": latest_processed_date
                }
            else:
                raise HTTPException(status_code=500, detail=f"Forecast failed: {result.stderr}")
        
        print(f"[UPDATE] New data available! Running pipeline for {latest_av_date}...")
        pipeline_result = subprocess.run(
            ["python", "/workspace/run_data_pipeline.py", "--date", latest_av_date],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes for full pipeline
        )
        
        if pipeline_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline failed: {pipeline_result.stderr}"
            )
        
        print("[UPDATE] Running multi-step forecast...")
        forecast_result = subprocess.run(
            ["python", "/workspace/multi_step_forecast.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if forecast_result.returncode != 0:
            print(f"[UPDATE] WARNING: Forecast failed but pipeline succeeded: {forecast_result.stderr}")
        
        return {
            "status": "updated",
            "message": f"Successfully updated with data through {latest_av_date}",
            "latest_alpha_vantage_date": latest_av_date,
            "previous_processed_date": latest_processed_date,
            "new_processed_date": latest_av_date
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Update timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")


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


