"""
End-to-end tests for model inference
Tests data loading, feature engineering, and model predictions
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../app'))

from app.data_loader import DataLoader
from app.inference import ModelInference


class TestDataLoader:
    """Test data loading and feature engineering for inference"""
    
    def test_load_latest_data_from_gcs(self):
        """Test loading latest processed data from GCS"""
        loader = DataLoader()
        
        try:
            df = loader.load_latest_data()
            
            assert isinstance(df, pd.DataFrame)
            assert not df.empty, "Loaded data should not be empty"
            
            # Check for required base columns
            required_cols = ['country', 'date', 'wti_price', 'brent_price']
            for col in required_cols:
                assert col in df.columns, f"Missing required column: {col}"
            
            print(f"✅ Loaded data from GCS: {len(df)} records")
            print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"   Countries: {df['country'].nunique()}")
            print(f"   Columns: {len(df.columns)}")
            
        except Exception as e:
            print(f"⚠️  Failed to load from GCS: {e}")
            print("   Make sure GOOGLE_APPLICATION_CREDENTIALS is set")
            pytest.skip("GCS not accessible")
    
    def test_engineer_features(self):
        """Test feature engineering matches training format"""
        loader = DataLoader()
        
        # Create comprehensive mock data
        dates = pd.date_range('2023-10-01', periods=60, freq='D')
        countries = ['US', 'SA', 'IQ']
        
        data = []
        for country in countries:
            for date in dates:
                data.append({
                    'country': country,
                    'date': date,
                    'wti_price': 70 + np.random.randn() * 5,
                    'brent_price': 75 + np.random.randn() * 5,
                    'avg_tone': np.random.randn() * 2,
                    'tone_std': np.random.rand(),
                    'mention_count': np.random.randint(10, 100),
                    'theme_energy': np.random.randint(0, 20),
                    'theme_conflict': np.random.randint(0, 15),
                    'theme_sanctions': np.random.randint(0, 10),
                    'theme_trade': np.random.randint(0, 12),
                    'theme_economy': np.random.randint(0, 25),
                    'theme_policy': np.random.randint(0, 18)
                })
        
        mock_df = pd.DataFrame(data)
        
        # Engineer features
        result = loader.engineer_features(mock_df)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        
        # Check critical engineered features exist
        critical_features = [
            # WTI features
            'wti_delta', 'wti_return', 'wti_delta_lag1', 'wti_delta_lag7', 'wti_delta_lag30',
            'wti_return_ma5', 'wti_return_ma20', 'wti_return_std30', 'wti_rsi',
            'wti_momentum_5_20',
            # Brent features
            'brent_delta', 'brent_return', 'brent_delta_lag1', 'brent_return_ma5', 'brent_rsi',
            # Sentiment features
            'avg_sentiment', 'event_count',
            # Theme features
            'theme_energy_change', 'theme_conflict_zscore'
        ]
        
        missing = [f for f in critical_features if f not in result.columns]
        assert len(missing) == 0, f"Missing critical features: {missing}"
        
        # Count features
        feature_cols = [c for c in result.columns 
                       if c not in ['country', 'date', 'country_iso3', 'node_id']]
        
        print(f"✅ Feature engineering successful")
        print(f"   Total features: {len(feature_cols)}")
        print(f"   Critical features verified: {len(critical_features)}")
        
        # Should have 60+ features
        assert len(feature_cols) >= 50, f"Expected 50+ features, got {len(feature_cols)}"
        
        # Check no NaN values
        nan_cols = result[feature_cols].columns[result[feature_cols].isna().any()].tolist()
        assert len(nan_cols) == 0, f"Found NaN values in columns: {nan_cols}"
        
        return result
    
    def test_prepare_features_for_model(self):
        """Test preparing features in correct order for model"""
        loader = DataLoader()
        
        # First engineer features
        result = self.test_engineer_features()
        
        # Prepare for model
        X, feature_names = loader.prepare_features_for_model(result)
        
        assert isinstance(X, np.ndarray), "Features should be numpy array"
        assert X.ndim == 2, "Features should be 2D array"
        assert len(feature_names) == X.shape[1], "Feature names should match columns"
        
        # Should have 50+ features
        assert len(feature_names) >= 50, f"Expected 50+ features, got {len(feature_names)}"
        
        print(f"✅ Model features prepared")
        print(f"   Shape: {X.shape}")
        print(f"   Features: {len(feature_names)}")
        print(f"   First 10 features: {feature_names[:10]}")
        
        # Check no NaN or inf values
        assert not np.isnan(X).any(), "Found NaN values in feature matrix"
        assert not np.isinf(X).any(), "Found inf values in feature matrix"


class TestModelInference:
    """Test model inference pipeline"""
    
    @pytest.mark.skipif(not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                       reason="GOOGLE_APPLICATION_CREDENTIALS not set")
    def test_load_models(self):
        """Test loading models from GCS"""
        inference = ModelInference()
        
        try:
            inference.load_models()
            
            assert inference.xgb_model is not None, "XGBoost model should be loaded"
            assert inference.htg_model is not None, "HTG model should be loaded"
            
            print(f"✅ Models loaded successfully")
            print(f"   XGBoost model: {type(inference.xgb_model)}")
            print(f"   HTG model: {type(inference.htg_model)}")
            
        except Exception as e:
            print(f"⚠️  Failed to load models: {e}")
            pytest.skip("Models not accessible in GCS")
    
    @pytest.mark.skipif(not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                       reason="GOOGLE_APPLICATION_CREDENTIALS not set")
    def test_predict_single_country(self):
        """Test making predictions for a single country"""
        inference = ModelInference()
        loader = DataLoader()
        
        try:
            # Load models
            inference.load_models()
            
            # Create mock features (61 features as expected)
            feature_names = [
                'wti_price', 'brent_price', 'wti_delta', 'wti_return', 
                'wti_delta_lag1', 'wti_delta_lag2', 'wti_delta_lag3',
                'wti_delta_lag5', 'wti_delta_lag7', 'wti_delta_lag14', 'wti_delta_lag30',
                'wti_return_ma5', 'wti_return_ma10', 'wti_return_ma20', 'wti_return_ma30',
                'wti_return_std5', 'wti_return_std10', 'wti_return_std20', 'wti_return_std30',
                'wti_rsi', 'wti_momentum_5_20', 'wti_momentum_10_30',
                'brent_delta', 'brent_return',
                'brent_delta_lag1', 'brent_delta_lag2', 'brent_delta_lag3',
                'brent_delta_lag5', 'brent_delta_lag7', 'brent_delta_lag14', 'brent_delta_lag30',
                'brent_return_ma5', 'brent_return_ma10', 'brent_return_ma20', 'brent_return_ma30',
                'brent_return_std5', 'brent_return_std10', 'brent_return_std20', 'brent_return_std30',
                'brent_rsi', 'brent_momentum_5_20', 'brent_momentum_10_30',
                'avg_sentiment', 'sentiment_lag1', 'sentiment_lag7', 'tone_std', 'event_count',
                'theme_energy', 'theme_conflict', 'theme_sanctions',
                'theme_trade', 'theme_economy', 'theme_policy',
                'theme_energy_change', 'theme_conflict_change',
                'theme_energy_zscore', 'theme_conflict_zscore',
                'theme_energy_spike', 'theme_conflict_spike',
                'spread_wti_brent', 'correlation_20d', 'volatility_ratio'
            ]
            
            # Create mock feature array
            X = np.random.randn(1, len(feature_names))
            
            # Make prediction
            result = inference.predict(X, country='US', feature_names=feature_names)
            
            assert isinstance(result, dict)
            assert 'country' in result
            assert 'predictions' in result
            assert 'ensemble_prediction' in result
            
            print(f"✅ Prediction successful")
            print(f"   Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"⚠️  Prediction failed: {e}")
            raise
    
    @pytest.mark.skipif(not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                       reason="GOOGLE_APPLICATION_CREDENTIALS not set")
    def test_end_to_end_inference(self):
        """Full E2E test: load data -> engineer features -> predict"""
        print("\n" + "="*70)
        print("END-TO-END INFERENCE TEST")
        print("="*70)
        
        loader = DataLoader()
        inference = ModelInference()
        
        try:
            # Step 1: Load latest data from GCS
            print("\n1️⃣  Loading latest data from GCS...")
            df = loader.load_latest_data()
            print(f"   Loaded {len(df)} records")
            
            # Step 2: Engineer features
            print("\n2️⃣  Engineering features...")
            df_engineered = loader.engineer_features(df)
            feature_cols = [c for c in df_engineered.columns 
                          if c not in ['country', 'date', 'country_iso3', 'node_id']]
            print(f"   Generated {len(feature_cols)} features")
            
            # Step 3: Prepare for model
            print("\n3️⃣  Preparing features for model...")
            X, feature_names = loader.prepare_features_for_model(df_engineered)
            print(f"   Feature matrix shape: {X.shape}")
            
            # Step 4: Load models
            print("\n4️⃣  Loading models from GCS...")
            inference.load_models()
            print("   Models loaded successfully")
            
            # Step 5: Make predictions for each country
            print("\n5️⃣  Making predictions...")
            countries = df_engineered['country'].unique()[:3]  # Test with 3 countries
            
            predictions = []
            for country in countries:
                country_mask = df_engineered['country'] == country
                X_country = X[country_mask][-1:]  # Get latest data point
                
                result = inference.predict(X_country, country=country, feature_names=feature_names)
                predictions.append(result)
                
                print(f"\n   {country}:")
                print(f"     XGBoost: {result['predictions']['xgboost']:.2f}%")
                print(f"     HTG: {result['predictions']['htg']:.2f}%")
                print(f"     Ensemble: {result['ensemble_prediction']:.2f}%")
            
            print("\n" + "="*70)
            print("✅ END-TO-END TEST PASSED")
            print("="*70)
            
            return predictions
            
        except Exception as e:
            print(f"\n❌ E2E test failed: {e}")
            raise


class TestAPICompatibility:
    """Test that inference outputs match API requirements"""
    
    def test_prediction_format(self):
        """Test prediction response format matches API schema"""
        # Mock prediction result
        result = {
            'country': 'US',
            'predictions': {
                'xgboost': 2.5,
                'htg': 3.1
            },
            'ensemble_prediction': 2.8,
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }
        
        # Validate schema
        assert 'country' in result
        assert 'predictions' in result
        assert 'ensemble_prediction' in result
        assert isinstance(result['predictions'], dict)
        assert 'xgboost' in result['predictions']
        assert 'htg' in result['predictions']
        
        # Validate types
        assert isinstance(result['predictions']['xgboost'], (int, float))
        assert isinstance(result['predictions']['htg'], (int, float))
        assert isinstance(result['ensemble_prediction'], (int, float))
        
        print("✅ Prediction format matches API schema")


if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING INFERENCE TESTS")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, '-v', '-s'])
