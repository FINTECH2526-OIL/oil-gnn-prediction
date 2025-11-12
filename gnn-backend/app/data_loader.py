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
        """Apply the same feature engineering as training - EXACTLY matching model_training.py"""
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
        df['brent_return'] = df.groupby('country_iso3')['brent_price'].pct_change()
        df['brent_delta'] = df.groupby('country_iso3')['brent_price'].diff()
        
        # Lag features (1, 2, 3, 5, 7, 14, 30)
        for lag in [1, 2, 3, 5, 7, 14, 30]:
            df[f'wti_delta_lag{lag}'] = df.groupby('country_iso3')['wti_delta'].shift(lag)
            df[f'wti_return_lag{lag}'] = df.groupby('country_iso3')['wti_return'].shift(lag)
            df[f'brent_delta_lag{lag}'] = df.groupby('country_iso3')['brent_delta'].shift(lag)
            df[f'brent_return_lag{lag}'] = df.groupby('country_iso3')['brent_return'].shift(lag)
        
        # Moving averages and std (5, 10, 20, 30)
        for window in [5, 10, 20, 30]:
            df[f'wti_return_ma{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
            df[f'wti_return_std{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).std())
            df[f'wti_delta_ma{window}'] = df.groupby('country_iso3')['wti_delta'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
            
            df[f'brent_return_ma{window}'] = df.groupby('country_iso3')['brent_return'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
            df[f'brent_return_std{window}'] = df.groupby('country_iso3')['brent_return'].transform(
                lambda x: x.rolling(window, min_periods=1).std())
            df[f'brent_delta_ma{window}'] = df.groupby('country_iso3')['brent_delta'].transform(
                lambda x: x.rolling(window, min_periods=1).mean())
        
        # Momentum features
        df['wti_momentum_5_20'] = df['wti_return_ma5'] - df['wti_return_ma20']
        df['wti_momentum_10_30'] = df['wti_return_ma10'] - df['wti_return_ma30']
        df['brent_momentum_5_20'] = df['brent_return_ma5'] - df['brent_return_ma20']
        df['brent_momentum_10_30'] = df['brent_return_ma10'] - df['brent_return_ma30']
        
        # RSI for WTI and Brent
        for price_col in ['wti_price', 'brent_price']:
            delta = df.groupby('country_iso3')[price_col].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.groupby(df['country_iso3']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            avg_loss = loss.groupby(df['country_iso3']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            df[f'{price_col.replace("_price", "")}_rsi'] = 100 - (100 / (1 + rs))
        
        # GDELT/Event features - check for both naming conventions
        if 'avg_sentiment' in df.columns:
            for lag in [1, 2, 3, 5, 7]:
                df[f'sentiment_lag{lag}'] = df.groupby('country_iso3')['avg_sentiment'].shift(lag)
        elif 'avg_tone' in df.columns:
            df['avg_sentiment'] = df['avg_tone']
            for lag in [1, 2, 3, 5, 7]:
                df[f'sentiment_lag{lag}'] = df.groupby('country_iso3')['avg_sentiment'].shift(lag)
        
        if 'tone_std' in df.columns:
            for lag in [1, 7]:
                df[f'tone_std_lag{lag}'] = df.groupby('country_iso3')['tone_std'].shift(lag)
        
        if 'event_count' in df.columns:
            for lag in [1, 7]:
                df[f'event_count_lag{lag}'] = df.groupby('country_iso3')['event_count'].shift(lag)
        elif 'mention_count' in df.columns:
            df['event_count'] = df['mention_count']
            for lag in [1, 7]:
                df[f'event_count_lag{lag}'] = df.groupby('country_iso3')['event_count'].shift(lag)
        
        # Price spread and correlation features
        if 'wti_price' in df.columns and 'brent_price' in df.columns:
            df['spread_wti_brent'] = df['wti_price'] - df['brent_price']
            
            # Rolling correlation - fixed to avoid multi-column issues
            corr_values = []
            for country in df['country_iso3'].unique():
                country_data = df[df['country_iso3'] == country].copy()
                country_corr = country_data['wti_return'].rolling(20, min_periods=10).corr(country_data['brent_return'])
                corr_values.extend(country_corr.tolist())
            df['correlation_20d'] = corr_values
            
            # Volatility ratio
            wti_vol = df.groupby('country_iso3')['wti_return'].transform(lambda x: x.rolling(20, min_periods=10).std())
            brent_vol = df.groupby('country_iso3')['brent_return'].transform(lambda x: x.rolling(20, min_periods=10).std())
            df['volatility_ratio'] = wti_vol / (brent_vol + 1e-8)
        
        # Theme features - ONLY for energy and conflict (model only uses these 2)
        for col in ['theme_energy', 'theme_conflict']:
            if col in df.columns and df[col].dtype != 'object':
                df[f'{col}_change'] = df.groupby('country_iso3')[col].diff()
                
                # Z-score for anomaly detection
                rolling_mean = df.groupby('country_iso3')[col].transform(lambda x: x.rolling(20, min_periods=5).mean())
                rolling_std = df.groupby('country_iso3')[col].transform(lambda x: x.rolling(20, min_periods=5).std())
                df[f'{col}_zscore'] = (df[col] - rolling_mean) / (rolling_std + 1e-8)
                df[f'{col}_spike'] = (df[f'{col}_zscore'] > 2).astype(int)
        
        # CRITICAL: Ensure all base columns exist (for backward compatibility with old GCS data)
        required_base_columns = {
            'tone_std': 0.0,
            'event_count': 0,
            'avg_sentiment': 0.0,
            'theme_energy': 0,
            'theme_conflict': 0,
            'theme_sanctions': 0,
            'theme_trade': 0,
            'theme_economy': 0,
            'theme_policy': 0
        }
        
        for col, default_value in required_base_columns.items():
            if col not in df.columns:
                df[col] = default_value
        
        # Target features (for compatibility with training, won't be used in prediction)
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

