import os
from pathlib import Path

class Config:
    GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "gdelt_raw_3_years")
    GCS_PROCESSED_PATH = os.environ.get("GCS_PROCESSED_PATH", "processed_data/")
    GCS_MODELS_PATH = os.environ.get("GCS_MODELS_PATH", "trained_models/")
    
    MODEL_RUN_ID = os.environ.get("MODEL_RUN_ID", "run_20251101_090727_18dd2c")
    
    LOCAL_CACHE_DIR = Path("/tmp/oil_model_cache")
    LOCAL_CACHE_DIR.mkdir(exist_ok=True, parents=True)
    
    PREDICTION_TEMPERATURE = float(os.environ.get("PREDICTION_TEMPERATURE", "0.25"))
    TOP_COUNTRIES_COUNT = int(os.environ.get("TOP_COUNTRIES_COUNT", "15"))
    
    PORT = int(os.environ.get("PORT", "8080"))
    HOST = os.environ.get("HOST", "0.0.0.0")
    
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

config = Config()
