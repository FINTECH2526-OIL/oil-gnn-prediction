import gzip
import json
import pandas as pd
import numpy as np
import pycountry
from datetime import datetime
from google.cloud import storage
from pathlib import Path
from .config import config

class DataLoader:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(config.GCS_BUCKET_NAME)
        
    def download_latest_data(self):
        blobs = list(self.client.list_blobs(config.GCS_BUCKET_NAME, prefix=config.GCS_PROCESSED_PATH))
        final_blobs = [b for b in blobs if b.name.startswith(f"{config.GCS_PROCESSED_PATH}final_aligned_data_") 
                      and b.name.endswith(".json.gz")]
        final_blobs_sorted = sorted(final_blobs, key=lambda b: b.name, reverse=True)
        
        if not final_blobs_sorted:
            raise FileNotFoundError("No final_aligned_data_*.json.gz found in GCS")
        
        latest_blob = final_blobs_sorted[0]
        local_path = config.LOCAL_CACHE_DIR / "latest_final_aligned_data.json.gz"
        
        with open(local_path, "wb") as f:
            f.write(latest_blob.download_as_bytes())
        
        return local_path
    
    def engineer_features(self, df):
        """Apply the same feature engineering as training"""
        # Add country_iso3 if not exists
        if 'country_iso3' not in df.columns:
            def to_iso3(name):
                try:
                    c = pycountry.countries.lookup(name)
                    return c.alpha_3
                except Exception:
                    s = str(name).upper()
                    s2 = "".join([c for c in s if c.isalpha() or c==" "]).strip().replace(" ", "_")
                    return s2
            
            df["country_iso3"] = df["country"].fillna("UNKNOWN").apply(to_iso3)
        
        # Sort by country and date
        df = df.sort_values(['country_iso3', 'date']).reset_index(drop=True)
        
        # Convert prices to numeric
        for col in ['wti_price', 'brent_price']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Basic price features
        df['wti_return'] = df.groupby('country_iso3')['wti_price'].pct_change()
        df['wti_delta'] = df.groupby('country_iso3')['wti_price'].diff()
        
        # Lag features
        for lag in [1, 2, 3, 5, 7, 14, 30]:
            df[f'wti_delta_lag{lag}'] = df.groupby('country_iso3')['wti_delta'].shift(lag)
            df[f'wti_return_lag{lag}'] = df.groupby('country_iso3')['wti_return'].shift(lag)
        
        # Moving averages and std
        for window in [5, 10, 20, 30]:
            df[f'wti_return_ma{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
            df[f'wti_return_std{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).std())
            df[f'wti_delta_ma{window}'] = df.groupby('country_iso3')['wti_delta'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
        
        # Momentum features
        df['wti_momentum_5_20'] = df['wti_return_ma5'] - df['wti_return_ma20']
        df['wti_momentum_10_30'] = df['wti_return_ma10'] - df['wti_return_ma30']
        
        # Target features (for compatibility, won't be used in prediction)
        df['wti_delta_next'] = df.groupby('country_iso3')['wti_delta'].shift(-1)
        df['wti_return_next'] = df.groupby('country_iso3')['wti_return'].shift(-1)
        
        return df
    
    def load_and_preprocess(self, local_path):
        with gzip.open(local_path, "rt", encoding="utf-8") as f:
            raw = f.read()
        
        records = json.loads(raw)
        df = pd.DataFrame.from_records(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # Engineer features like training
        df = self.engineer_features(df)
        
        return df
    
    def get_latest_data(self):
        local_path = self.download_latest_data()
        df = self.load_and_preprocess(local_path)
        return df
    
    def get_today_features(self, df, feature_cols):
        latest_date = df['date'].max()
        today_data = df[df['date'] == latest_date].copy()
        
        if today_data.empty:
            raise ValueError(f"No data found for latest date: {latest_date}")
        
        X_today = today_data[feature_cols].fillna(0).values
        
        return X_today, today_data, latest_date

