#!/usr/bin/env python3
"""
Backfill prediction history for the last 30 days.
This script generates predictions for historical dates and stores them in GCS.
"""

import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging

# Add the current directory to path for imports
sys.path.insert(0, '/workspace')

from app.config import config
from app.data_loader import load_latest_data
from app.inference import ModelInference
from google.cloud import storage
import json
import gzip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SGT = ZoneInfo("Asia/Singapore")

def _next_business_day(date_obj):
    """Get next business day (skip weekends)."""
    next_day = date_obj + timedelta(days=1)
    while next_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
        next_day += timedelta(days=1)
    return next_day

def _to_business_day(target_date):
    """Roll back to Friday if weekend."""
    while target_date.weekday() >= 5:
        target_date -= timedelta(days=1)
    return target_date

def backfill_historical_predictions(days_back=30):
    """
    Generate predictions for the last N business days.
    
    Args:
        days_back: Number of days to backfill (default 30)
    """
    try:
        logger.info(f"Starting backfill for last {days_back} days...")
        
        # Initialize storage client
        client = storage.Client()
        bucket = client.bucket(config.GCS_BUCKET_NAME)
        
        # Load model once
        logger.info("Loading model...")
        model_inf = ModelInference()
        
        # Get today in SGT
        today_sgt = datetime.now(SGT).date()
        today_business = _to_business_day(today_sgt)
        
        history = []
        
        # Generate predictions for each business day
        current_date = today_business
        count = 0
        
        while count < days_back:
            # Roll back to business day
            current_date = _to_business_day(current_date)
            
            try:
                logger.info(f"Processing date: {current_date}")
                
                # Load data for this date
                df, feature_cols = load_latest_data(target_date=current_date)
                
                if df is None or df.empty:
                    logger.warning(f"No data available for {current_date}, skipping...")
                    current_date -= timedelta(days=1)
                    continue
                
                # Get prediction
                result = model_inf.get_prediction_with_explanation(df, feature_cols)
                
                # Get reference close price (most recent in data)
                reference_close = df['wti_close'].iloc[-1]
                
                # Calculate predicted close
                predicted_close = reference_close + result["predicted_delta"]
                
                # Get next business day for prediction target
                prediction_for_date = _next_business_day(current_date)
                
                # Create prediction record
                record = {
                    "feature_date": current_date.isoformat(),
                    "prediction_for_date": prediction_for_date.isoformat(),
                    "reference_close": float(reference_close),
                    "predicted_delta": float(result["predicted_delta"]),
                    "predicted_close": float(predicted_close),
                    "total_abs_contribution": float(result["total_abs_contribution"]),
                    "num_countries": result["num_countries"],
                    "top_contributors": [
                        {
                            "country": country,
                            "contribution": float(data["contribution"]),
                            "percentage": float(data["percentage"]),
                            "raw_prediction": float(data["raw_prediction"]),
                            "attention_weight": float(data["attention_weight"])
                        }
                        for country, data in list(result["top_contributors"].items())[:15]
                    ],
                    "prediction_generated_at": datetime.now(SGT).isoformat()
                }
                
                history.append(record)
                count += 1
                logger.info(f"✓ Generated prediction for {current_date} → {prediction_for_date}")
                
            except Exception as e:
                logger.error(f"Error processing {current_date}: {e}")
            
            # Move to previous day
            current_date -= timedelta(days=1)
        
        # Sort by date (newest first)
        history.sort(key=lambda x: x["feature_date"], reverse=True)
        
        # Save to GCS
        history_path = f"{config.GCS_PROCESSED_PATH}predictions/history.json"
        blob = bucket.blob(history_path)
        
        json_data = json.dumps(history, indent=2)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        blob.upload_from_string(
            compressed_data,
            content_type='application/json',
            content_encoding='gzip'
        )
        
        logger.info(f"✓ Saved {len(history)} predictions to {history_path}")
        logger.info(f"Date range: {history[-1]['feature_date']} to {history[0]['feature_date']}")
        
        return {
            "success": True,
            "records_created": len(history),
            "oldest_date": history[-1]['feature_date'],
            "newest_date": history[0]['feature_date']
        }
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Backfill prediction history')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backfill (default: 30)')
    args = parser.parse_args()
    
    result = backfill_historical_predictions(days_back=args.days)
    print(json.dumps(result, indent=2))
