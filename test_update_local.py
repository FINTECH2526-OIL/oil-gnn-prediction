#!/usr/bin/env python3
"""Test the /update logic locally before deploying"""
import os
import sys
from datetime import date
import requests

# Set environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'manifest-vault-470110-k5'
os.environ['GCP_PROJECT_ID'] = 'manifest-vault-470110-k5'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'WY4DN5PO5LQ3INPJ'
os.environ['GCS_BUCKET_NAME'] = 'gdelt_raw_3_years'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gnn-backend'))

from google.cloud import storage
from app.config import config

def test_update_logic():
    """Test the update logic without running full pipeline"""
    
    print("="*60)
    print("TESTING UPDATE LOGIC LOCALLY")
    print("="*60)
    
    today = date.today()
    print(f"\n1. Today is: {today}")
    
    # Step 1: Check Alpha Vantage
    print("\n2. Checking Alpha Vantage for latest data...")
    alpha_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    
    response = requests.get(
        f"https://www.alphavantage.co/query?function=WTI&interval=daily&apikey={alpha_key}",
        timeout=10
    )
    av_data = response.json()
    
    if "data" not in av_data:
        print(f"   ❌ No data from Alpha Vantage: {av_data}")
        return
    
    # Get latest valid date
    latest_av_date = None
    for item in av_data["data"]:
        try:
            if item.get("value") and item["value"] != ".":
                latest_av_date = item["date"]
                break
        except:
            continue
    
    print(f"   ✓ Latest Alpha Vantage date: {latest_av_date}")
    
    # Step 2: Check our latest processed data
    print("\n3. Checking latest processed data in GCS...")
    client = storage.Client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    
    blobs = list(bucket.list_blobs(prefix='processed_data/final_aligned_data_'))
    if not blobs:
        print("   ❌ No processed files found")
        latest_processed_date = None
    else:
        latest_blob = max(blobs, key=lambda b: b.name)
        # Extract date from filename: final_aligned_data_YYYYMMDD.json.gz
        date_str = latest_blob.name.split('_')[-1].replace('.json.gz', '')
        latest_processed_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        print(f"   ✓ Latest processed date: {latest_processed_date}")
        print(f"   File: {latest_blob.name}")
    
    # Step 3: Decision
    print("\n4. Decision:")
    needs_update = latest_processed_date is None or latest_av_date > latest_processed_date
    
    if needs_update:
        print(f"   ✓ NEEDS UPDATE: {latest_av_date} > {latest_processed_date}")
        print(f"   Would run: python run_data_pipeline.py --date {latest_av_date}")
        print(f"   Then run: python multi_step_forecast.py")
    else:
        print(f"   ✓ UP TO DATE: {latest_processed_date} >= {latest_av_date}")
        print(f"   Would only run: python multi_step_forecast.py")
    
    # Step 4: Check if scripts exist
    print("\n5. Checking if scripts exist locally...")
    scripts = [
        'run_data_pipeline.py',
        'multi_step_forecast.py',
        'incremental_update.py'
    ]
    
    for script in scripts:
        path = os.path.join(os.path.dirname(__file__), script)
        if os.path.exists(path):
            print(f"   ✓ {script} exists")
        else:
            print(f"   ❌ {script} NOT FOUND")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        test_update_logic()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
