import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gnn-backend'))

from app.daily_data_pipeline import DailyDataPipeline
from prediction_pipeline import run_daily_inference

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run daily data pipeline manually')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD), defaults to yesterday')
    parser.add_argument('--days-back', type=int, default=30, help='Number of historical days to fetch')
    
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        target_date = datetime.now() - timedelta(days=1)
    
    print(f"Running data pipeline for {target_date.date()}")
    print(f"Fetching {args.days_back} days of historical data")
    print("=" * 60)
    
    pipeline = DailyDataPipeline()
    
    try:
        output_path = pipeline.run_daily_update(target_date)
        inference_result = run_daily_inference()
        
        print("=" * 60)
        print("SUCCESS!")
        print(f"Data saved to: gs://{os.environ.get('GCS_BUCKET_NAME', 'gdelt_raw_3_years')}/{output_path}")
        record = inference_result.get('record', {})
        feature_date = record.get('feature_date')
        predicted_close = record.get('predicted_close')
        predicted_delta = record.get('predicted_delta')
        print(f"Processed feature date: {feature_date}")
        print(f"Predicted delta: {predicted_delta}")
        print(f"Predicted next close: {predicted_close}")
        print(f"History entries: {inference_result.get('history_length')} (updated {inference_result.get('updated_outcomes')} outcomes)")
        
    except Exception as e:
        print("=" * 60)
        print("ERROR!")
        print(f"Failed to run pipeline: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
