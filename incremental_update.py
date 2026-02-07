#!/usr/bin/env python3
"""Incremental data pipeline - only fetch missing days"""
import sys
import os
from datetime import datetime, timedelta
import json
import gzip

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gnn-backend'))

from app.daily_data_pipeline import DailyDataPipeline
from prediction_pipeline import run_daily_inference

def main():
    print("Incremental update: Fetching only Dec 4 and Dec 5...")
    
    pipeline = DailyDataPipeline()
    target_date = datetime(2025, 12, 5)
    
    # Load Dec 3 cache
    print("Loading Dec 3 GDELT cache...")
    gdelt_data_list = pipeline._load_cached_gdelt_data("20251203")
    if gdelt_data_list is None:
        print("ERROR: Dec 3 cache not found!")
        sys.exit(1)
    
    print(f"Loaded {len(gdelt_data_list)} days from cache (Nov 3 - Dec 3)")
    
    # Load oil cache (Dec 5 already has it)
    print("Loading oil price cache...")
    oil_data = pipeline._load_cached_oil_data("20251205")
    if oil_data is None:
        print("Fetching fresh oil prices...")
        oil_data = pipeline.fetch_oil_prices(days_back=90)
        pipeline._save_cached_oil_data(oil_data, "20251205")
    else:
        print(f"Using cached oil prices: {len(oil_data)} days")
    
    # Fetch only Dec 4 and Dec 5 GDELT
    print("\nFetching GDELT for Dec 4...")
    dec4 = datetime(2025, 12, 4)
    gdelt_df_dec4 = pipeline.fetch_gdelt_for_date(dec4)
    if not gdelt_df_dec4.empty:
        processed_dec4 = pipeline.process_gdelt_data(gdelt_df_dec4, dec4)
        if processed_dec4:
            gdelt_data_list.append(processed_dec4)
            print(f"✓ Added Dec 4: {processed_dec4['total_articles']} articles")
    
    print("Fetching GDELT for Dec 5...")
    dec5 = datetime(2025, 12, 5)
    gdelt_df_dec5 = pipeline.fetch_gdelt_for_date(dec5)
    if not gdelt_df_dec5.empty:
        processed_dec5 = pipeline.process_gdelt_data(gdelt_df_dec5, dec5)
        if processed_dec5:
            gdelt_data_list.append(processed_dec5)
            print(f"✓ Added Dec 5: {processed_dec5['total_articles']} articles")
    
    # Save updated cache
    print("\nSaving updated cache...")
    pipeline._save_cached_gdelt_data(gdelt_data_list, "20251205")
    
    # Now process everything
    print(f"\nTotal GDELT data: {len(gdelt_data_list)} days (Nov 3 - Dec 5)")
    
    print("Aligning and engineering features...")
    final_df = pipeline.align_and_engineer_features(gdelt_data_list, oil_data)
    
    if final_df.empty:
        raise ValueError("No data generated from pipeline")
    
    from app.config import config
    output_filename = f"final_aligned_data_{target_date.date().strftime('%Y%m%d')}.json.gz"
    output_path = f"{config.GCS_PROCESSED_PATH}{output_filename}"
    
    records = final_df.to_dict('records')
    json_data = json.dumps(records, ensure_ascii=False, default=str)
    compressed_data = gzip.compress(json_data.encode('utf-8'))
    
    blob = pipeline.bucket.blob(output_path)
    blob.upload_from_string(compressed_data, content_type='application/gzip')
    
    print(f"\n✓ Saved processed data to GCS: {output_path}")
    print(f"  Total records: {len(records)}")
    print(f"  Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    
    # Run inference
    print("\nRunning inference to generate prediction...")
    inference_result = run_daily_inference()
    
    print("\n" + "="*60)
    print("SUCCESS!")
    print(f"Data saved to: gs://gdelt_raw_3_years/{output_path}")
    record = inference_result.get('record', {})
    print(f"Prediction for: {record.get('prediction_for_date')}")
    print(f"Predicted close: ${record.get('predicted_close'):.2f}")
    print(f"Predicted delta: ${record.get('predicted_delta'):.2f}")
    print(f"History entries: {inference_result.get('history_length')}")
    print("="*60)

if __name__ == "__main__":
    main()
