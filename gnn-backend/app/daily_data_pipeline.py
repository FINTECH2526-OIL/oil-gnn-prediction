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

from .config import config

class DailyDataPipeline:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(config.GCS_BUCKET_NAME)
        self.alpha_vantage_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        
    def fetch_gdelt_for_date(self, target_date: datetime) -> pd.DataFrame:
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
        columns = [
            'GKGRECORDID', 'V21DATE', 'V2SOURCECOLLECTIONIDENTIFIER', 'V2SOURCECOMMONNAME',
            'V2DOCUMENTIDENTIFIER', 'V1COUNTS', 'V21COUNTS', 'V1THEMES', 'V21THEMES',
            'V1LOCATIONS', 'V21LOCATIONS', 'V1PERSONS', 'V21PERSONS', 'V1ORGANIZATIONS',
            'V21ORGANIZATIONS', 'V1TONE', 'V21TONE', 'V1DATES', 'V21DATES', 'V1GCAM',
            'V21SHARINGIMAGE', 'V21RELATEDIMAGES', 'V21SOCIALIMAGEEMBEDS', 'V21SOCIALVIDEOEMBEDS',
            'V21QUOTATIONS', 'V21ALLNAMES', 'V21AMOUNTS', 'V21TRANSLATIONINFO', 'V21EXTRAS'
        ]
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    csv_filename = z.namelist()[0]
                    with z.open(csv_filename) as csvfile:
                        df = pd.read_csv(csvfile, sep='\t', names=columns,
                                       dtype=str, low_memory=False, encoding='utf-8',
                                       on_bad_lines='skip')
                        return df
            elif response.status_code == 404:
                return None
        except Exception as e:
            return None
        
        return None
    
    def fetch_oil_prices(self, days_back: int = 90) -> pd.DataFrame:
        if not self.alpha_vantage_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "WTI",
            "interval": "daily",
            "apikey": self.alpha_vantage_key
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if "data" not in data:
            raise ValueError(f"Alpha Vantage API error: {data}")
        
        records = []
        for item in data["data"]:
            records.append({
                "date": pd.to_datetime(item["date"]),
                "wti_price": float(item["value"])
            })
        
        df = pd.DataFrame(records)
        df = df.sort_values("date").reset_index(drop=True)
        
        url_brent = f"https://www.alphavantage.co/query"
        params_brent = {
            "function": "BRENT",
            "interval": "daily",
            "apikey": self.alpha_vantage_key
        }
        
        response_brent = requests.get(url_brent, params=params_brent, timeout=30)
        data_brent = response_brent.json()
        
        if "data" in data_brent:
            brent_records = []
            for item in data_brent["data"]:
                brent_records.append({
                    "date": pd.to_datetime(item["date"]),
                    "brent_price": float(item["value"])
                })
            
            df_brent = pd.DataFrame(brent_records)
            df = df.merge(df_brent, on="date", how="left")
        
        return df
    
    def process_gdelt_data(self, df: pd.DataFrame, target_date: datetime) -> Dict:
        if df.empty:
            return {}
        
        df = df.copy()
        df['V21DATE'] = pd.to_datetime(df['V21DATE'], format='%Y%m%d%H%M%S', errors='coerce')
        df = df.dropna(subset=['V21DATE'])
        
        countries = []
        for locations in df['V21LOCATIONS'].fillna(''):
            countries.extend(self._extract_countries(locations))
        
        country_counts = pd.Series(countries).value_counts()
        
        tone_values = []
        for tone_str in df['V21TONE'].fillna(''):
            tone_metrics = self._extract_tone(tone_str)
            tone_values.append(tone_metrics['tone'])
        
        themes = []
        for theme_str in df['V21THEMES'].fillna(''):
            themes.extend([t.strip() for t in theme_str.split(';') if t.strip()])
        
        theme_counts = pd.Series(themes).value_counts()
        
        result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'total_articles': len(df),
            'avg_tone': np.mean(tone_values) if tone_values else 0.0,
            'tone_std': np.std(tone_values) if tone_values else 0.0,
            'num_countries': len(country_counts),
            'top_countries': country_counts.head(50).to_dict(),
            'top_themes': theme_counts.head(100).to_dict()
        }
        
        return result
    
    def _extract_countries(self, locations_str: str) -> List[str]:
        if not locations_str:
            return []
        
        countries = []
        try:
            location_entries = locations_str.split(';')
            for entry in location_entries:
                if '#' in entry:
                    parts = entry.split('#')
                    if len(parts) >= 3:
                        country_code = parts[2]
                        if country_code and len(country_code) == 2:
                            try:
                                country = pycountry.countries.get(alpha_2=country_code.upper())
                                if country:
                                    countries.append(country.alpha_3)
                            except:
                                pass
        except:
            pass
        
        return countries
    
    def _extract_tone(self, tone_str: str) -> Dict[str, float]:
        tone_dict = {
            'tone': 0.0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'polarity': 0.0,
            'word_count': 0
        }
        
        if not tone_str:
            return tone_dict
        
        try:
            parts = tone_str.split(',')
            if len(parts) >= 1:
                tone_dict['tone'] = float(parts[0])
            if len(parts) >= 2:
                tone_dict['positive_score'] = float(parts[1])
            if len(parts) >= 3:
                tone_dict['negative_score'] = float(parts[2])
            if len(parts) >= 4:
                tone_dict['polarity'] = float(parts[3])
            if len(parts) >= 7:
                tone_dict['word_count'] = int(float(parts[6]))
        except:
            pass
        
        return tone_dict
    
    def align_and_engineer_features(self, gdelt_data: List[Dict], oil_data: pd.DataFrame) -> pd.DataFrame:
        gdelt_df = pd.DataFrame(gdelt_data)
        gdelt_df['date'] = pd.to_datetime(gdelt_df['date'])
        
        oil_data['date'] = pd.to_datetime(oil_data['date'])
        
        merged = oil_data.merge(gdelt_df, on='date', how='left')
        
        for col in ['wti_price', 'brent_price']:
            if col in merged.columns:
                merged[col] = merged[col].fillna(method='ffill')
        
        country_data = []
        for idx, row in merged.iterrows():
            date = row['date']
            wti_price = row.get('wti_price', 0)
            brent_price = row.get('brent_price', 0)
            
            if pd.notna(row.get('top_countries')) and isinstance(row['top_countries'], dict):
                for country, count in row['top_countries'].items():
                    country_data.append({
                        'date': date,
                        'country': country,
                        'wti_price': wti_price,
                        'brent_price': brent_price,
                        'article_count': count,
                        'avg_tone': row.get('avg_tone', 0),
                        'tone_std': row.get('tone_std', 0)
                    })
        
        df = pd.DataFrame(country_data)
        
        if df.empty:
            return df
        
        df = df.sort_values(['country', 'date']).reset_index(drop=True)
        
        df['country_iso3'] = df['country']
        
        for col in ['wti_price', 'brent_price']:
            if col in df.columns:
                df[f'{col}_lag1'] = df.groupby('country_iso3')[col].shift(1)
                df[f'{col}_lag2'] = df.groupby('country_iso3')[col].shift(2)
                df[f'{col}_lag7'] = df.groupby('country_iso3')[col].shift(7)
        
        df['wti_return'] = df.groupby('country_iso3')['wti_price'].pct_change()
        df['wti_delta'] = df.groupby('country_iso3')['wti_price'].diff()
        
        for window in [5, 10, 20, 30]:
            df[f'wti_return_ma{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
            df[f'wti_return_std{window}'] = df.groupby('country_iso3')['wti_return'].transform(
                lambda x: x.rolling(window, min_periods=1).std()
            )
        
        df['wti_momentum_5_20'] = df['wti_return_ma5'] - df['wti_return_ma20']
        
        df['wti_rsi'] = df.groupby('country_iso3')['wti_return'].transform(
            lambda x: 100 - 100/(1 + x.rolling(14).apply(
                lambda y: (y>0).sum()/(y<0).sum() if (y<0).sum()>0 else 1
            ))
        )
        
        df['article_count_lag1'] = df.groupby('country_iso3')['article_count'].shift(1)
        df['article_count_change'] = df.groupby('country_iso3')['article_count'].pct_change()
        
        df['tone_lag1'] = df.groupby('country_iso3')['avg_tone'].shift(1)
        df['tone_change'] = df.groupby('country_iso3')['avg_tone'].diff()
        
        return df
    
    def run_daily_update(self, target_date: Optional[datetime] = None) -> str:
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)
        
        print(f"Running daily data pipeline for {target_date.date()}")
        
        oil_data = self.fetch_oil_prices(days_back=90)
        print(f"Fetched oil prices: {len(oil_data)} days")
        
        gdelt_data_list = []
        for days_ago in range(30, -1, -1):
            date = target_date - timedelta(days=days_ago)
            print(f"Fetching GDELT data for {date.date()}...")
            
            gdelt_df = self.fetch_gdelt_for_date(date)
            if not gdelt_df.empty:
                processed = self.process_gdelt_data(gdelt_df, date)
                if processed:
                    gdelt_data_list.append(processed)
            
            time.sleep(1)
        
        print(f"Processed GDELT data for {len(gdelt_data_list)} days")
        
        final_df = self.align_and_engineer_features(gdelt_data_list, oil_data)
        
        if final_df.empty:
            raise ValueError("No data generated from pipeline")
        
        output_filename = f"final_aligned_data_{target_date.strftime('%Y%m%d')}.json.gz"
        output_path = f"{config.GCS_PROCESSED_PATH}{output_filename}"
        
        records = final_df.to_dict('records')
        json_data = json.dumps(records, ensure_ascii=False, default=str)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        blob = self.bucket.blob(output_path)
        blob.upload_from_string(compressed_data, content_type='application/gzip')
        
        print(f"Saved processed data to GCS: {output_path}")
        print(f"Total records: {len(records)}")
        print(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
        
        return output_path
