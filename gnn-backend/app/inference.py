import joblib
import numpy as np
import pandas as pd
import json
from pathlib import Path
from google.cloud import storage
from .config import config
from .models import CountryTemporalModels
import sys

# Make CountryTemporalModels available in __main__ for pickle compatibility
if hasattr(sys.modules['__main__'], '__file__'):
    sys.modules['__main__'].CountryTemporalModels = CountryTemporalModels

class ModelInference:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(config.GCS_BUCKET_NAME)
        self.models_loaded = False
        self.feature_columns = None
        
    def download_model_artifacts(self):
        artifacts_prefix = f"{config.GCS_MODELS_PATH}{config.MODEL_RUN_ID}/artifacts/"
        
        required_files = [
            "model_base.pkl",
            "model_enhanced.pkl",
            "country_models.obj",
            "scaler_X.pkl",
            "adjacency.npy",
            "metadata.json"
        ]
        
        local_model_dir = config.LOCAL_CACHE_DIR / config.MODEL_RUN_ID
        local_model_dir.mkdir(exist_ok=True, parents=True)
        
        for filename in required_files:
            blob_name = artifacts_prefix + filename
            local_path = local_model_dir / filename
            
            if not local_path.exists():
                blob = self.bucket.blob(blob_name)
                if blob.exists():
                    with open(local_path, "wb") as f:
                        f.write(blob.download_as_bytes())
        
        return local_model_dir
    
    def load_models(self):
        if self.models_loaded:
            return
        
        model_dir = self.download_model_artifacts()
        
        self.model_base = joblib.load(model_dir / "model_base.pkl")
        self.model_enhanced = joblib.load(model_dir / "model_enhanced.pkl")
        self.country_models = joblib.load(model_dir / "country_models.obj")
        self.scaler_X = joblib.load(model_dir / "scaler_X.pkl")
        self.adjacency = np.load(model_dir / "adjacency.npy")
        
        metadata_path = model_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_columns = metadata.get('feature_columns', None)
                if self.feature_columns:
                    print(f"Loaded {len(self.feature_columns)} features from metadata.json")
        
        # Fallback: Try to get feature names from scaler (sklearn >= 1.0)
        if self.feature_columns is None and hasattr(self.scaler_X, 'feature_names_in_'):
            self.feature_columns = self.scaler_X.feature_names_in_.tolist()
            print(f"Loaded {len(self.feature_columns)} features from scaler.feature_names_in_")
        
        # Last resort: Use all engineered features and hope for the best
        if self.feature_columns is None:
            print(f"WARNING: No feature list found in metadata or scaler!")
            print(f"Scaler expects {self.scaler_X.n_features_in_} features")
            print("Using all engineered features - this may cause errors")
            # Return empty so main.py uses all available features
            self.feature_columns = None
        
        self.models_loaded = True
    
    def predict_delta(self, X):
        self.load_models()
        
        X_scaled = self.scaler_X.transform(X)
        
        pred_base = self.model_base.predict(X_scaled)
        pred_enhanced = self.model_enhanced.predict(X_scaled)
        
        optimal_weight = 0.5
        final_pred = optimal_weight * pred_base + (1 - optimal_weight) * pred_enhanced
        
        return final_pred
    
    def predict_with_countries(self, df, feature_cols, date=None):
        self.load_models()
        
        if date is None:
            date = df['date'].max()
        
        date_data = df[df['date'] == date].copy()
        
        if date_data.empty:
            raise ValueError(f"No data for date {date}")
        
        # Determine which country column exists
        country_col = None
        for col in ['country_iso3', 'country_code', 'country']:
            if col in date_data.columns:
                country_col = col
                break
        
        if country_col is None:
            raise ValueError(f"No country column found. Available columns: {list(date_data.columns)}")
        
        country_predictions = {}
        
        for country_iso3 in date_data[country_col].unique():
            country_data = date_data[date_data[country_col] == country_iso3]
            
            if country_data.empty:
                continue
            
            X = country_data[feature_cols].fillna(0).values
            
            if hasattr(self.country_models, 'country_models') and country_iso3 in self.country_models.country_models:
                scaler = self.country_models.country_scalers[country_iso3]
                model = self.country_models.country_models[country_iso3]
                X_scaled = scaler.transform(X)
                pred = model.predict(X_scaled)[0]
            else:
                pred = self.predict_delta(X)[0]
            
            country_predictions[country_iso3] = float(pred)
        
        return country_predictions
    
    def compute_attention_weights(self, country_predictions):
        self.load_models()
        
        countries = list(country_predictions.keys())
        predictions = np.array([country_predictions[c] for c in countries])
        
        abs_preds = np.abs(predictions)
        weights = abs_preds / (abs_preds.sum() + 1e-8)
        
        attention_dict = {
            country: float(weight) 
            for country, weight in zip(countries, weights)
        }
        
        sorted_attention = dict(sorted(attention_dict.items(), key=lambda x: abs(x[1]), reverse=True))
        
        return sorted_attention
    
    def get_prediction_with_explanation(self, df, feature_cols, date=None):
        country_predictions = self.predict_with_countries(df, feature_cols, date)
        
        attention_weights = self.compute_attention_weights(country_predictions)
        
        weighted_pred = sum(country_predictions[c] * attention_weights[c] 
                          for c in country_predictions.keys())
        
        total_abs_contribution = sum(abs(country_predictions[c]) * attention_weights[c] 
                                    for c in country_predictions.keys())
        
        top_contributors = {}
        for country in list(attention_weights.keys())[:config.TOP_COUNTRIES_COUNT]:
            contribution = country_predictions[country] * attention_weights[country]
            percentage = (abs(contribution) / total_abs_contribution * 100) if total_abs_contribution > 0 else 0
            top_contributors[country] = {
                "contribution": float(contribution),
                "percentage": float(percentage),
                "raw_prediction": float(country_predictions[country]),
                "attention_weight": float(attention_weights[country])
            }
        
        return {
            "predicted_delta": float(weighted_pred),
            "total_abs_contribution": float(total_abs_contribution),
            "top_contributors": top_contributors,
            "num_countries": len(country_predictions)
        }
