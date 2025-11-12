import os
import pandas as pd
import numpy as np
import requests
import zipfile
import io
from datetime import datetime, timedelta
import time
import gzip
import json
from typing import List, Dict, Optional
from google.cloud import storage
import pycountry

class DailyDataPipeline:
    def __init__(self):
        self.client = storage.Client()
        bucket_name = os.environ.get("GCS_BUCKET_NAME", "gdelt_raw_3_years")
        self.bucket = self.client.bucket(bucket_name)
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        self.gcs_processed_path = os.environ.get("GCS_PROCESSED_PATH", "processed_data/")
        
    def fetch_gdelt_for_date(self, target_date: datetime) -> pd.DataFrame:
        """Fetch all GDELT GKG files for a given date (96 files, every 15 minutes)"""
        date_str = target_date.strftime('%Y%m%d')
        base_url = "http://data.gdeltproject.org/gdeltv2"
        all_records = []
        
        for hour in range(24):
            for minute in ['00', '15', '30', '45']:
                timestamp = f"{date_str}{hour:02d}{minute}00"
                url = f"{base_url}/{timestamp}.gkg.csv.zip"
                
                df = self._fetch_single_gdelt_file(url)
                if df is not None and not df.empty:
                    all_records.append(df)
        
        if all_records:
            combined_df = pd.concat(all_records, ignore_index=True)
            return combined_df
        
        return pd.DataFrame()
    
    def _fetch_single_gdelt_file(self, url: str) -> Optional[pd.DataFrame]:
        """Fetch and parse a single GDELT file with proper encoding handling"""
        columns = [
            'GKGRECORDID', 'V21DATE', 'V2SOURCECOLLECTIONIDENTIFIER', 'V2SOURCECOMMONNAME',
            'V2DOCUMENTIDENTIFIER', 'V1COUNTS', 'V21COUNTS', 'V1THEMES', 'V21THEMES',
            'V1LOCATIONS', 'V21LOCATIONS', 'V1PERSONS', 'V21PERSONS', 'V1ORGANIZATIONS',
            'V21ORGANIZATIONS', 'V1TONE', 'V21TONE', 'V1DATES', 'V21DATES', 'V1GCAM',
            'V21SHARINGIMAGE', 'V21RELATEDIMAGES', 'V21SOCIALIMAGEEMBEDS', 'V21SOCIALVIDEOEMBEDS',
            'V21QUOTATIONS', 'V21ALLNAMES', 'V21AMOUNTS', 'V21TRANSLATIONINFO', 'V2EXTRASXML'
        ]
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    csv_filename = z.namelist()[0]
                    with z.open(csv_filename) as csvfile:
                        try:
                            df = pd.read_csv(csvfile, sep='\t', names=columns,
                                          dtype=str, low_memory=False, encoding='utf-8')
                            return df
                        except UnicodeDecodeError:
                            csvfile.seek(0)
                            df = pd.read_csv(csvfile, sep='\t', names=columns,
                                          dtype=str, low_memory=False, encoding='latin-1')
                            return df
            elif response.status_code == 404:
                return None
            else:
                print(f"HTTP {response.status_code} for {url}")
                return None
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None
    
    def fetch_oil_prices(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch WTI and Brent oil prices from Alpha Vantage"""
        wti_data = self._fetch_alpha_vantage("WTI")
        time.sleep(15)  # Alpha Vantage free tier: max 5 calls/minute
        brent_data = self._fetch_alpha_vantage("BRENT")
        
        if wti_data is None or brent_data is None:
            raise Exception("Failed to fetch oil price data")
        
        wti_df = pd.DataFrame(wti_data['data'])
        brent_df = pd.DataFrame(brent_data['data'])
        
        wti_df['date'] = pd.to_datetime(wti_df['date'])
        brent_df['date'] = pd.to_datetime(brent_df['date'])
        
        wti_df = wti_df[(wti_df['date'] >= start_date) & (wti_df['date'] <= end_date)]
        brent_df = brent_df[(brent_df['date'] >= start_date) & (brent_df['date'] <= end_date)]
        
        merged = pd.merge(wti_df, brent_df, on='date', suffixes=('_wti', '_brent'))
        merged = merged.sort_values('date').reset_index(drop=True)
        
        return merged
    
    def _fetch_alpha_vantage(self, commodity: str) -> Optional[Dict]:
        """Fetch commodity data from Alpha Vantage API"""
        url = f"https://www.alphavantage.co/query?function={commodity}&interval=daily&apikey={self.alpha_vantage_key}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to fetch {commodity}: {e}")
            return None
    
    def process_gdelt_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract country-level features from GDELT data"""
        df = df[df['V21LOCATIONS'].notna()].copy()
        
        country_data = []
        for _, row in df.iterrows():
            locations = str(row['V21LOCATIONS']).split(';')
            tone_str = str(row['V21TONE'])
            
            try:
                tone_values = [float(x) for x in tone_str.split(',')]
                avg_tone = tone_values[0] if tone_values else 0
            except:
                avg_tone = 0
            
            for loc in locations:
                parts = loc.split('#')
                if len(parts) >= 3:
                    country_code = parts[2]
                    if country_code and len(country_code) == 2:
                        country_data.append({
                            'country': country_code,
                            'tone': avg_tone,
                            'date': pd.to_datetime(row['V21DATE'], format='%Y%m%d%H%M%S')
                        })
        
        if not country_data:
            return pd.DataFrame()
        
        country_df = pd.DataFrame(country_data)
        country_df['date'] = country_df['date'].dt.date
        
        agg = country_df.groupby(['country', 'date']).agg({
            'tone': ['mean', 'std', 'count']
        }).reset_index()
        
        agg.columns = ['country', 'date', 'avg_tone', 'tone_std', 'mention_count']
        agg['tone_std'] = agg['tone_std'].fillna(0)
        
        return agg
    
    def align_and_engineer_features(self, gdelt_df: pd.DataFrame, oil_df: pd.DataFrame) -> pd.DataFrame:
        """Align GDELT and oil price data, engineer features"""
        gdelt_df['date'] = pd.to_datetime(gdelt_df['date'])
        oil_df['date'] = pd.to_datetime(oil_df['date'])
        
        # Merge with oil prices
        merged = pd.merge(gdelt_df, oil_df, on='date', how='inner')
        
        # Convert oil prices to numeric
        for col in ['value_wti', 'value_brent']:
            merged[col] = pd.to_numeric(merged[col], errors='coerce')
        
        # Engineer features: lags, returns, moving averages, RSI
        merged = merged.sort_values(['country_code', 'date']).reset_index(drop=True)
        
        # Oil price features
        for col in ['value_wti', 'value_brent']:
            merged[f'{col}_lag1'] = merged.groupby('country')[col].shift(1)
            merged[f'{col}_lag7'] = merged.groupby('country')[col].shift(7)
            merged[f'{col}_return'] = merged.groupby('country')[col].pct_change()
            merged[f'{col}_ma7'] = merged.groupby('country')[col].transform(lambda x: x.rolling(7, min_periods=1).mean())
            merged[f'{col}_ma30'] = merged.groupby('country')[col].transform(lambda x: x.rolling(30, min_periods=1).mean())
        
        # GDELT features
        merged['tone_lag1'] = merged.groupby('country')['avg_tone'].shift(1)
        merged['tone_lag7'] = merged.groupby('country')['avg_tone'].shift(7)
        merged['mention_count_lag1'] = merged.groupby('country')['mention_count'].shift(1)
        
        # RSI calculation
        for col in ['value_wti', 'value_brent']:
            delta = merged.groupby('country')[col].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.groupby(merged['country']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            avg_loss = loss.groupby(merged['country']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            merged[f'{col}_rsi'] = 100 - (100 / (1 + rs))
        
        # Fill NaN values
        merged = merged.fillna(0)
        
        return merged
    
    def run_daily_update(self, target_date: datetime) -> str:
        """Run the complete daily data pipeline"""
        print(f"Starting daily update for {target_date.date()}")
        
        # Fetch GDELT data
        print("Fetching GDELT data...")
        gdelt_raw = self.fetch_gdelt_for_date(target_date)
        
        if gdelt_raw.empty:
            raise Exception(f"No GDELT data found for {target_date.date()}")
        
        print(f"Fetched {len(gdelt_raw)} GDELT records")
        
        # Process GDELT data
        print("Processing GDELT data...")
        gdelt_processed = self.process_gdelt_data(gdelt_raw)
        
        if gdelt_processed.empty:
            raise Exception("No valid country data extracted from GDELT")
        
        print(f"Processed to {len(gdelt_processed)} country-day records")
        
        # Fetch oil prices (need a range for lag features)
        start_date = target_date - timedelta(days=60)
        end_date = target_date + timedelta(days=1)
        
        print("Fetching oil prices...")
        oil_data = self.fetch_oil_prices(start_date, end_date)
        
        if oil_data.empty:
            raise Exception("No oil price data fetched")
        
        print(f"Fetched {len(oil_data)} days of oil prices")
        
        # Align and engineer features
        print("Engineering features...")
        final_data = self.align_and_engineer_features(gdelt_processed, oil_data)
        
        if final_data.empty:
            raise Exception("Feature engineering produced empty dataset")
        
        print(f"Final dataset: {len(final_data)} records")
        
        # Save to GCS
        date_str = target_date.strftime('%Y%m%d')
        output_filename = f"final_aligned_data_{date_str}.json.gz"
        output_path = f"{self.gcs_processed_path}{output_filename}"
        
        print(f"Saving to GCS: {output_path}")
        
        # Convert to JSON and compress
        json_data = final_data.to_json(orient='records', date_format='iso')
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        # Upload to GCS
        blob = self.bucket.blob(output_path)
        blob.upload_from_string(compressed_data, content_type='application/gzip')
        
        print(f"Successfully saved to gs://{self.bucket.name}/{output_path}")
        
        return output_path
