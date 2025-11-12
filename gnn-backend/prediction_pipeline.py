import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from google.cloud import storage

from app.config import config
from app.data_loader import DataLoader
from app.inference import ModelInference

HISTORY_BLOB_PATH = f"{config.GCS_PROCESSED_PATH}predictions/history.json"
HISTORY_WINDOW = 120  # retain roughly 6 months of records


def _next_business_day(day: pd.Timestamp) -> pd.Timestamp:
    next_day = day + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day


def _load_history(bucket: storage.Bucket) -> List[Dict]:
    blob = bucket.blob(HISTORY_BLOB_PATH)
    if not blob.exists():
        return []
    try:
        payload = blob.download_as_text()
        data = json.loads(payload)
        if isinstance(data, dict) and "records" in data:
            data = data["records"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _save_history(bucket: storage.Bucket, history: List[Dict]) -> None:
    blob = bucket.blob(HISTORY_BLOB_PATH)
    history_sorted = sorted(history, key=lambda r: r.get("feature_date", ""))[-HISTORY_WINDOW:]
    blob.upload_from_string(json.dumps(history_sorted, separators=(",", ":")))


def _prepare_feature_columns(model_inf: ModelInference, df: pd.DataFrame) -> List[str]:
    if model_inf.feature_columns is None:
        exclude_cols = {"country", "date"}
        return [
            c for c in df.columns
            if c not in exclude_cols and "next" not in c and "surprise" not in c and df[c].dtype != "object"
        ]

    feature_cols: List[str] = []
    missing_columns: List[str] = []
    for col in model_inf.feature_columns:
        if col in df.columns:
            feature_cols.append(col)
        else:
            missing_columns.append(col)
            df[col] = 0.0
            feature_cols.append(col)

    if missing_columns:
        print(
            f"WARNING: Added {len(missing_columns)} missing features with zeros: {missing_columns[:10]}",
            file=sys.stderr,
        )

    return feature_cols


def _generate_record(feature_df: pd.DataFrame, model_inf: ModelInference, target_ts: pd.Timestamp) -> Dict:
    feature_copy = feature_df.copy()
    feature_copy["date"] = pd.to_datetime(feature_copy["date"]).dt.normalize()

    reference_slice = feature_copy[feature_copy["date"] == target_ts]
    if reference_slice.empty:
        raise ValueError(f"No rows for target date {target_ts.date()} in engineered data")

    reference_close = float(reference_slice["wti_price"].iloc[0])
    feature_cols = _prepare_feature_columns(model_inf, feature_copy)
    meta_cols = [c for c in ["country", "country_iso3", "date"] if c in feature_copy.columns]
    feature_copy = feature_copy[meta_cols + feature_cols]

    inference_result = model_inf.get_prediction_with_explanation(feature_copy, feature_cols, date=target_ts)
    predicted_delta = float(inference_result["predicted_delta"])
    predicted_close = reference_close + predicted_delta
    next_business = _next_business_day(target_ts)

    top_contributors = [
        {
            "country": country,
            "contribution": float(values["contribution"]),
            "percentage": float(values["percentage"]),
            "raw_prediction": float(values["raw_prediction"]),
            "attention_weight": float(values["attention_weight"]),
        }
        for country, values in inference_result.get("top_contributors", {}).items()
    ]

    now_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "feature_date": str(target_ts.date()),
        "prediction_for_date": str(next_business.date()),
        "reference_close": reference_close,
        "predicted_delta": predicted_delta,
        "predicted_close": predicted_close,
        "total_abs_contribution": float(inference_result.get("total_abs_contribution", 0.0)),
        "num_countries": int(inference_result.get("num_countries", 0)),
        "top_contributors": top_contributors,
        "prediction_generated_at": now_utc,
    }


def run_daily_inference(target_date: Optional[datetime] = None) -> Dict:
    """Load latest engineered data, execute inference, and update prediction history."""
    loader = DataLoader()
    df = loader.get_latest_data()

    if df.empty:
        raise ValueError("No engineered data available for inference")

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    latest_date = df["date"].max()

    if target_date is not None:
        target_ts = pd.Timestamp(target_date).normalize()
    else:
        target_ts = latest_date

    if target_ts > latest_date:
        raise ValueError(
            f"Requested target {target_ts.date()} is in the future of available data {latest_date.date()}"
        )

    model_inf = ModelInference()
    model_inf.load_models()

    record = _generate_record(df, model_inf, target_ts)

    client = storage.Client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    history = _load_history(bucket)

    # Update prior predictions with actual outcome when available
    updated_outcomes = 0
    for past_record in history:
        if past_record.get("prediction_for_date") == record["feature_date"] and past_record.get("actual_close") is None:
            past_record["actual_close"] = record["reference_close"]
            past_record["actual_delta"] = record["reference_close"] - past_record.get("reference_close", record["reference_close"])
            past_record["error_delta"] = past_record.get("predicted_delta") - past_record["actual_delta"]
            past_record["error_price"] = past_record.get("predicted_close") - record["reference_close"]
            past_record["actual_recorded_at"] = record["prediction_generated_at"]
            updated_outcomes += 1

    # Deduplicate record for current feature date
    existing = next((item for item in history if item.get("feature_date") == record["feature_date"]), None)
    if existing:
        existing.update(record)
    else:
        history.append(record)

    _save_history(bucket, history)

    return {
        "record": record,
        "history_length": len(history),
        "updated_outcomes": updated_outcomes,
        "history_blob": HISTORY_BLOB_PATH,
    }
