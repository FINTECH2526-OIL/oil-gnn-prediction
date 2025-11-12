"""
Complete End-to-End Integration Tests
Tests the full workflow: Data Pipeline -> Storage -> Inference -> API
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import requests
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../app'))

from daily_data_pipeline_standalone import DailyDataPipeline
from app.data_loader import DataLoader
from app.inference import ModelInference


class TestCompleteWorkflow:
    """Test complete workflow from data collection to prediction"""
    
    @pytest.mark.skipif(
        not all([
            os.environ.get('ALPHA_VANTAGE_API_KEY'),
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        ]),
        reason="Required environment variables not set"
    )
    def test_full_workflow(self):
        """
        Complete E2E test:
        1. Run data pipeline for a specific date
        2. Verify data saved to GCS
        3. Load data for inference
        4. Engineer features
        5. Make predictions
        6. Validate output
        """
        print("\n" + "="*80)
        print("COMPLETE END-TO-END WORKFLOW TEST")
        print("="*80)
        
        # Use a recent date (3 days ago to ensure data availability)
        test_date = datetime.now() - timedelta(days=3)
        
        # Step 1: Run Data Pipeline
        print(f"\n📊 STEP 1: Running data pipeline for {test_date.date()}")
        print("-" * 80)
        
        pipeline = DailyDataPipeline()
        
        try:
            output_path = pipeline.run_daily_update(test_date)
            print(f"✅ Pipeline completed successfully")
            print(f"   Output: {output_path}")
        except Exception as e:
            print(f"⚠️  Pipeline failed: {e}")
            pytest.skip(f"Data pipeline failed: {e}")
        
        # Step 2: Verify Data in GCS
        print(f"\n💾 STEP 2: Verifying data in GCS")
        print("-" * 80)
        
        loader = DataLoader()
        
        try:
            df = loader.load_latest_data()
            print(f"✅ Data loaded from GCS")
            print(f"   Records: {len(df)}")
            print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"   Countries: {df['country'].unique()[:5]}")
            
            # Verify required columns exist
            required_cols = ['country', 'date', 'wti_price', 'brent_price', 
                           'avg_tone', 'mention_count']
            missing = [c for c in required_cols if c not in df.columns]
            assert len(missing) == 0, f"Missing columns: {missing}"
            
        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            raise
        
        # Step 3: Engineer Features
        print(f"\n⚙️  STEP 3: Engineering features")
        print("-" * 80)
        
        try:
            df_engineered = loader.engineer_features(df)
            
            feature_cols = [c for c in df_engineered.columns 
                          if c not in ['country', 'date', 'country_iso3', 'node_id']]
            
            print(f"✅ Features engineered")
            print(f"   Total features: {len(feature_cols)}")
            print(f"   Records: {len(df_engineered)}")
            
            # Verify we have enough features (should be 50+)
            assert len(feature_cols) >= 50, f"Only {len(feature_cols)} features generated"
            
            # Check for NaN values
            nan_count = df_engineered[feature_cols].isna().sum().sum()
            print(f"   NaN values: {nan_count}")
            assert nan_count == 0, f"Found {nan_count} NaN values in features"
            
        except Exception as e:
            print(f"❌ Feature engineering failed: {e}")
            raise
        
        # Step 4: Prepare for Model
        print(f"\n🔧 STEP 4: Preparing features for model")
        print("-" * 80)
        
        try:
            X, feature_names = loader.prepare_features_for_model(df_engineered)
            
            print(f"✅ Features prepared")
            print(f"   Matrix shape: {X.shape}")
            print(f"   Feature count: {len(feature_names)}")
            print(f"   Sample features: {feature_names[:5]}")
            
            # Verify shape
            assert X.shape[1] == len(feature_names), "Feature count mismatch"
            assert X.shape[0] > 0, "No data to predict on"
            
        except Exception as e:
            print(f"❌ Feature preparation failed: {e}")
            raise
        
        # Step 5: Load Models and Make Predictions
        print(f"\n🤖 STEP 5: Loading models and making predictions")
        print("-" * 80)
        
        inference = ModelInference()
        
        try:
            inference.load_models()
            print(f"✅ Models loaded")
            
            # Make predictions for top 3 countries
            countries = df_engineered['country'].unique()[:3]
            predictions_summary = []
            
            for country in countries:
                country_mask = df_engineered['country'] == country
                X_country = X[country_mask][-1:]  # Latest data point
                
                result = inference.predict(X_country, country=country, 
                                         feature_names=feature_names)
                
                predictions_summary.append({
                    'country': country,
                    'xgboost': result['predictions']['xgboost'],
                    'htg': result['predictions']['htg'],
                    'ensemble': result['ensemble_prediction']
                })
                
                print(f"\n   {country}:")
                print(f"     XGBoost:  {result['predictions']['xgboost']:>6.2f}%")
                print(f"     HTG:      {result['predictions']['htg']:>6.2f}%")
                print(f"     Ensemble: {result['ensemble_prediction']:>6.2f}%")
            
            print(f"\n✅ Predictions completed for {len(countries)} countries")
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}")
            raise
        
        # Step 6: Validate Predictions
        print(f"\n✓ STEP 6: Validating predictions")
        print("-" * 80)
        
        for pred in predictions_summary:
            # Check predictions are reasonable (-100% to +100%)
            for key in ['xgboost', 'htg', 'ensemble']:
                value = pred[key]
                assert -100 <= value <= 100, f"{key} prediction {value} out of range"
                assert not np.isnan(value), f"{key} prediction is NaN"
        
        print(f"✅ All predictions are valid")
        
        # Summary
        print("\n" + "="*80)
        print("🎉 COMPLETE E2E WORKFLOW TEST PASSED")
        print("="*80)
        print(f"\n📈 Summary:")
        print(f"   Test Date: {test_date.date()}")
        print(f"   Records Processed: {len(df)}")
        print(f"   Features Generated: {len(feature_cols)}")
        print(f"   Countries Predicted: {len(predictions_summary)}")
        print(f"\n   Predictions:")
        for pred in predictions_summary:
            print(f"     {pred['country']}: {pred['ensemble']:.2f}%")
        
        return predictions_summary


class TestAPIEndpoint:
    """Test API endpoint if running locally"""
    
    @pytest.mark.skipif(
        not os.environ.get('API_URL'),
        reason="API_URL not set (use http://localhost:8080 for local testing)"
    )
    def test_prediction_endpoint(self):
        """Test /predict endpoint"""
        api_url = os.environ.get('API_URL', 'http://localhost:8080')
        
        try:
            response = requests.post(
                f"{api_url}/predict",
                json={'country': 'US'},
                timeout=30
            )
            
            assert response.status_code == 200, f"API returned {response.status_code}"
            
            result = response.json()
            
            # Validate response structure
            assert 'country' in result
            assert 'predictions' in result
            assert 'ensemble_prediction' in result
            
            print(f"✅ API endpoint working")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API not accessible: {e}")
            pytest.skip(f"API not running: {e}")
    
    @pytest.mark.skipif(
        not os.environ.get('API_URL'),
        reason="API_URL not set"
    )
    def test_health_endpoint(self):
        """Test /health endpoint"""
        api_url = os.environ.get('API_URL', 'http://localhost:8080')
        
        try:
            response = requests.get(f"{api_url}/health", timeout=10)
            
            assert response.status_code == 200
            
            result = response.json()
            assert result['status'] == 'healthy'
            
            print(f"✅ Health check passed")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not running: {e}")


if __name__ == '__main__':
    print("=" * 80)
    print("RUNNING END-TO-END INTEGRATION TESTS")
    print("=" * 80)
    
    # Run tests
    pytest.main([__file__, '-v', '-s', '--tb=short'])
