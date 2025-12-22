#!/usr/bin/env python3
"""
Multi-step forecasting: Predict Dec 2, 3, 4, 5, 6 iteratively.
Uses predicted oil prices to generate next-day features.
NO API CALLS - uses cached data only.
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import gzip
from google.cloud import storage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gnn-backend'))

from app.config import config
from app.data_loader import DataLoader
from app.inference import ModelInference
from app.daily_data_pipeline import DailyDataPipeline

def load_latest_data():
    """Load the most recent processed data file."""
    client = storage.Client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    
    # Find latest processed file
    blobs = list(bucket.list_blobs(prefix='processed_data/final_aligned_data_'))
    if not blobs:
        raise ValueError("No processed data files found")
    
    latest_blob = max(blobs, key=lambda b: b.name)
    print(f"Loading: {latest_blob.name}")
    
    data = gzip.decompress(latest_blob.download_as_bytes())
    records = json.loads(data)
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"Loaded {len(df)} records, date range: {df['date'].min()} to {df['date'].max()}")
    return df

def get_latest_oil_price(df):
    """Get the most recent oil price."""
    latest_date = df['date'].max()
    latest_data = df[df['date'] == latest_date]
    wti_price = latest_data['wti_price'].iloc[0]
    return latest_date, wti_price

def predict_next_day(df, model_inf, feature_cols):
    """Make prediction for next day."""
    result = model_inf.get_prediction_with_explanation(df, feature_cols)
    return result['predicted_delta'], result

def add_synthetic_day(df, new_date, predicted_wti_price):
    """
    Add a synthetic day with predicted oil price.
    Forward-fill GDELT features from latest day.
    """
    latest_date = df['date'].max()
    latest_day = df[df['date'] == latest_date].copy()
    
    # Update to new date and predicted price
    latest_day['date'] = new_date
    latest_day['wti_price'] = predicted_wti_price
    latest_day['brent_price'] = predicted_wti_price * 1.08  # Approximate Brent spread
    
    # Recalculate oil-derived features for the new price
    # This is simplified - ideally we'd recalculate all lags and rolling windows
    # But for forecasting, we use the most recent features as proxy
    
    return pd.concat([df, latest_day], ignore_index=True)

def multi_step_forecast(start_date, num_days=5):
    """
    Perform multi-step forecasting.
    
    Args:
        start_date: Date of the latest known data (e.g., Dec 1)
        num_days: Number of days to forecast ahead (default 5)
    """
    print(f"\n{'='*60}")
    print(f"MULTI-STEP FORECAST: {num_days} days ahead from {start_date}")
    print(f"{'='*60}\n")
    
    # Load initial data
    df = load_latest_data()
    
    # Initialize model
    model_inf = ModelInference()
    model_inf.load_models()
    
    # Use model's feature columns if available, otherwise default
    if model_inf.feature_columns is not None:
        feature_cols = []
        missing_from_df = []
        for col in model_inf.feature_columns:
            if col in df.columns:
                feature_cols.append(col)
            else:
                missing_from_df.append(col)
                df[col] = 0.0  # Backfill missing features
                feature_cols.append(col)
        
        if missing_from_df:
            print(f"Backfilled {len(missing_from_df)} missing features with zeros")
    else:
        # Fallback to default feature selection
        exclude_cols = ['country', 'date', 'country_iso3']
        feature_cols = [c for c in df.columns 
                       if c not in exclude_cols
                       and 'next' not in c 
                       and 'surprise' not in c
                       and df[c].dtype != 'object']
    
    print(f"Using {len(feature_cols)} features for prediction\n")
    
    # Get starting point
    current_date, current_wti_price = get_latest_oil_price(df)
    print(f"Starting from: {current_date.date()} with WTI=${current_wti_price:.2f}\n")
    
    predictions = []
    
    for i in range(num_days):
        forecast_date = current_date + timedelta(days=1)
        
        print(f"Step {i+1}/{num_days}: Predicting {forecast_date.date()}")
        print(f"  Current WTI: ${current_wti_price:.2f}")
        
        # Make prediction
        predicted_delta, result = predict_next_day(df, model_inf, feature_cols)
        predicted_wti_price = current_wti_price + predicted_delta
        
        print(f"  Predicted delta: ${predicted_delta:.2f}")
        print(f"  Predicted WTI: ${predicted_wti_price:.2f}")
        print(f"  Contributing countries: {result['num_countries']}\n")
        
        # Convert top_contributors dict to array format for frontend
        contributors_array = [
            {
                'country': country,
                'contribution': data['contribution'],
                'percentage': data['percentage'],
                'raw_prediction': data['raw_prediction'],
                'attention_weight': data['attention_weight']
            }
            for country, data in result['top_contributors'].items()
        ]
        
        # Store prediction
        predictions.append({
            'feature_date': current_date.strftime('%Y-%m-%d'),
            'prediction_for_date': forecast_date.strftime('%Y-%m-%d'),
            'reference_close': current_wti_price,
            'predicted_delta': predicted_delta,
            'predicted_close': predicted_wti_price,
            'num_countries': result['num_countries'],
            'top_contributors': contributors_array,
            'total_abs_contribution': result['total_abs_contribution'],
            'prediction_generated_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        })
        
        # Add synthetic day for next iteration
        df = add_synthetic_day(df, forecast_date, predicted_wti_price)
        
        # Update current state
        current_date = forecast_date
        current_wti_price = predicted_wti_price
    
    return predictions

def save_predictions_to_history(predictions):
    """Save predictions to GCS history file."""
    client = storage.Client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    history_blob_path = f"{config.GCS_PROCESSED_PATH}predictions/history.json"
    blob = bucket.blob(history_blob_path)
    
    # Load existing history
    try:
        if blob.exists():
            content = blob.download_as_text()
            history = json.loads(content)
            if isinstance(history, dict) and "records" in history:
                history = history["records"]
        else:
            history = []
    except:
        history = []
    
    # Add new predictions (avoid duplicates)
    existing_dates = {(h.get('feature_date'), h.get('prediction_for_date')) for h in history}
    
    for pred in predictions:
        key = (pred['feature_date'], pred['prediction_for_date'])
        if key not in existing_dates:
            history.append(pred)
            print(f"Added prediction: {pred['feature_date']} → {pred['prediction_for_date']}")
    
    # Sort by feature_date descending
    history_sorted = sorted(history, key=lambda x: x.get('feature_date', ''), reverse=True)
    
    # Save back
    blob.upload_from_string(json.dumps(history_sorted, indent=2), content_type='application/json')
    print(f"\n✓ Saved {len(predictions)} new predictions to {history_blob_path}")

def main():
    print("Multi-Step Forecasting (NO API CALLS)")
    print("Using cached data only - FREE!\n")
    
    # Run forecast
    predictions = multi_step_forecast(
        start_date=datetime(2025, 12, 1),  # Latest data we have
        num_days=5  # Predict Dec 2, 3, 4, 5, 6
    )
    
    # Display results
    print(f"\n{'='*60}")
    print("FORECAST SUMMARY")
    print(f"{'='*60}")
    for pred in predictions:
        direction = "↑" if pred['predicted_delta'] > 0 else "↓"
        print(f"{pred['prediction_for_date']}: ${pred['predicted_close']:.2f} "
              f"({direction} ${abs(pred['predicted_delta']):.2f})")
    
    # Save to history
    save_predictions_to_history(predictions)
    
    print(f"\n✓ SUCCESS! Dashboard will now show predictions through Dec 6")
    print("Refresh your frontend to see the updated forecast.")

if __name__ == "__main__":
    main()
