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
        """Extract country-level features from GDELT data including themes"""
        df = df[df['V21LOCATIONS'].notna()].copy()
        
        country_data = []
        for _, row in df.iterrows():
            locations = str(row['V21LOCATIONS']).split(';')
            tone_str = str(row['V21TONE'])
            themes_str = str(row.get('V21THEMES', ''))
            
            # Extract tone metrics
            try:
                tone_values = [float(x) for x in tone_str.split(',')]
                avg_tone = tone_values[0] if tone_values else 0
                tone_std = tone_values[3] if len(tone_values) > 3 else 0
            except:
                avg_tone = 0
                tone_std = 0
            
            # Categorize themes
            theme_counts = {'ENERGY': 0, 'CONFLICT': 0, 'SANCTIONS': 0, 'TRADE': 0, 'ECONOMY': 0, 'POLICY': 0}
            if themes_str and themes_str.lower() != 'nan':
                themes = themes_str.split(';')[:10]  # Limit to first 10 themes
                for theme in themes:
                    theme_cat = self._get_theme_category(theme)
                    if theme_cat in theme_counts:
                        theme_counts[theme_cat] += 1
            
            # Extract countries from locations
            for loc in locations:
                parts = loc.split('#')
                if len(parts) >= 3:
                    country_code = parts[2]
                    if country_code and len(country_code) == 2:
                        record = {
                            'country': country_code,
                            'tone': avg_tone,
                            'tone_std': tone_std,
                            'date': pd.to_datetime(row['V21DATE'], format='%Y%m%d%H%M%S'),
                        }
                        # Add theme counts
                        record.update({f'theme_{k.lower()}': v for k, v in theme_counts.items()})
                        country_data.append(record)
        
        if not country_data:
            return pd.DataFrame()
        
        country_df = pd.DataFrame(country_data)
        country_df['date'] = country_df['date'].dt.date
        
        # Aggregate by country and date
        agg_dict = {
            'tone': ['mean', 'std', 'count'],
        }
        # Add theme columns to aggregation
        for theme in ['theme_energy', 'theme_conflict', 'theme_sanctions', 'theme_trade', 'theme_economy', 'theme_policy']:
            if theme in country_df.columns:
                agg_dict[theme] = 'sum'
        
        agg = country_df.groupby(['country', 'date']).agg(agg_dict).reset_index()
        
        # Flatten column names
        new_cols = ['country', 'date', 'avg_tone', 'tone_std', 'mention_count']
        for theme in ['theme_energy', 'theme_conflict', 'theme_sanctions', 'theme_trade', 'theme_economy', 'theme_policy']:
            if theme in country_df.columns:
                new_cols.append(theme)
        
        agg.columns = new_cols
        agg['tone_std'] = agg['tone_std'].fillna(0)
        
        return agg
    
    def _get_theme_category(self, theme: str) -> str:
        """Categorize GDELT themes into major categories"""
        theme_upper = theme.upper()
        
        if any(x in theme_upper for x in ['OIL', 'ENERGY', 'GAS', 'PETROLEUM', 'FUEL', 'MINING', 'ECON_ENERGY', 'OILPRICE']):
            return 'ENERGY'
        elif any(x in theme_upper for x in ['WAR', 'CONFLICT', 'MILITARY', 'ARMED', 'VIOLENCE', 'KILL', 'ATTACK', 'TERROR']):
            return 'CONFLICT'
        elif any(x in theme_upper for x in ['SANCTION', 'EMBARGO', 'BLOCKADE', 'RESTRICTION']):
            return 'SANCTIONS'
        elif any(x in theme_upper for x in ['TRADE', 'EXPORT', 'IMPORT', 'TARIFF', 'COMMERCE']):
            return 'TRADE'
        elif any(x in theme_upper for x in ['ECON_', 'ECONOMY', 'INFLATION', 'CURRENCY', 'FINANCE', 'MARKET']):
            return 'ECONOMY'
        elif any(x in theme_upper for x in ['GOVERNMENT', 'POLICY', 'REGULATION', 'LAW', 'LEGAL']):
            return 'POLICY'
        else:
            return 'OTHER'
    
    def align_and_engineer_features(self, gdelt_df: pd.DataFrame, oil_df: pd.DataFrame) -> pd.DataFrame:
        """Align GDELT and oil price data, engineer features matching training format"""
        gdelt_df['date'] = pd.to_datetime(gdelt_df['date'])
        oil_df['date'] = pd.to_datetime(oil_df['date'])
        
        # Rename oil columns to match training format
        oil_df = oil_df.rename(columns={
            'value_wti': 'wti_price',
            'value_brent': 'brent_price'
        })
        
        # Merge with oil prices
        merged = pd.merge(gdelt_df, oil_df, on='date', how='inner')
        
        # Convert oil prices to numeric
        for col in ['wti_price', 'brent_price']:
            merged[col] = pd.to_numeric(merged[col], errors='coerce')
        
        # Engineer features: lags, returns, moving averages, RSI
        merged = merged.sort_values(['country', 'date']).reset_index(drop=True)
        
        # Oil price features - match training format
        for col in ['wti_price', 'brent_price']:
            # Returns and deltas
            merged[f'{col.replace("_price", "")}_return'] = merged.groupby('country')[col].pct_change()
            merged[f'{col.replace("_price", "")}_delta'] = merged.groupby('country')[col].diff()
            
            # Lags (1, 2, 3, 5, 7, 14, 30)
            for lag in [1, 2, 3, 5, 7, 14, 30]:
                merged[f'{col.replace("_price", "")}_delta_lag{lag}'] = merged.groupby('country')[f'{col.replace("_price", "")}_delta'].shift(lag)
                merged[f'{col.replace("_price", "")}_return_lag{lag}'] = merged.groupby('country')[f'{col.replace("_price", "")}_return'].shift(lag)
            
            # Moving averages (5, 10, 20, 30)
            for window in [5, 10, 20, 30]:
                merged[f'{col.replace("_price", "")}_return_ma{window}'] = merged.groupby('country')[f'{col.replace("_price", "")}_return'].transform(
                    lambda x: x.rolling(window, min_periods=1).mean())
                merged[f'{col.replace("_price", "")}_return_std{window}'] = merged.groupby('country')[f'{col.replace("_price", "")}_return'].transform(
                    lambda x: x.rolling(window, min_periods=1).std())
                merged[f'{col.replace("_price", "")}_delta_ma{window}'] = merged.groupby('country')[f'{col.replace("_price", "")}_delta'].transform(
                    lambda x: x.rolling(window, min_periods=1).mean())
            
            # RSI calculation
            delta = merged.groupby('country')[col].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.groupby(merged['country']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            avg_loss = loss.groupby(merged['country']).transform(lambda x: x.rolling(14, min_periods=1).mean())
            
            rs = avg_gain / avg_loss.replace(0, np.nan)
            merged[f'{col.replace("_price", "")}_rsi'] = 100 - (100 / (1 + rs))
        
        # Momentum features
        if 'wti_return_ma5' in merged.columns and 'wti_return_ma20' in merged.columns:
            merged['wti_momentum_5_20'] = merged['wti_return_ma5'] - merged['wti_return_ma20']
        if 'wti_return_ma10' in merged.columns and 'wti_return_ma30' in merged.columns:
            merged['wti_momentum_10_30'] = merged['wti_return_ma10'] - merged['wti_return_ma30']
        
        # GDELT/Sentiment features with proper naming
        if 'avg_tone' in merged.columns:
            merged['avg_sentiment'] = merged['avg_tone']  # Rename for consistency
            for lag in [1, 2, 3, 5, 7]:
                merged[f'avg_sentiment_lag{lag}'] = merged.groupby('country')['avg_sentiment'].shift(lag)
        
        if 'tone_std' in merged.columns:
            for lag in [1, 7]:
                merged[f'tone_std_lag{lag}'] = merged.groupby('country')['tone_std'].shift(lag)
        
        if 'mention_count' in merged.columns:
            merged['event_count'] = merged['mention_count']  # Rename for consistency
            for lag in [1, 7]:
                merged[f'event_count_lag{lag}'] = merged.groupby('country')['event_count'].shift(lag)
        
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
