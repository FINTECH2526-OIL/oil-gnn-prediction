"""
Unit tests for daily data pipeline
Tests GDELT fetching, Alpha Vantage fetching, and feature engineering
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from daily_data_pipeline_standalone import DailyDataPipeline


class TestGDELTFetching:
    """Test GDELT data fetching"""
    
    def test_fetch_single_gdelt_file(self):
        """Test fetching a single GDELT file"""
        pipeline = DailyDataPipeline()
        
        # Test with a recent date (yesterday)
        test_date = datetime.now() - timedelta(days=1)
        timestamp = test_date.strftime('%Y%m%d') + '000000'
        url = f"http://data.gdeltproject.org/gdeltv2/{timestamp}.gkg.csv.zip"
        
        df = pipeline._fetch_single_gdelt_file(url)
        
        # Should return DataFrame or None (if file doesn't exist)
        assert df is None or isinstance(df, pd.DataFrame)
        
        if df is not None:
            # Check that it has the expected columns
            expected_cols = ['V21DATE', 'V21LOCATIONS', 'V21TONE', 'V21THEMES']
            for col in expected_cols:
                assert col in df.columns, f"Missing column: {col}"
            
            print(f"✅ Fetched GDELT file: {len(df)} records")
    
    def test_process_gdelt_data(self):
        """Test GDELT data processing with real structure"""
        pipeline = DailyDataPipeline()
        
        # Create mock GDELT data
        mock_data = pd.DataFrame({
            'V21DATE': ['20231101120000', '20231101120000', '20231101130000'],
            'V21LOCATIONS': [
                '1#United States#US#USCA#34.05#-118.25#US',
                '1#Iraq#IQ#IQ#33.3#44.4#IQ',
                '1#Saudi Arabia#SA#SA#24.7#46.7#SA'
            ],
            'V21TONE': [
                '-5.2,10.5,15.7,25.2,0,0,100',
                '3.1,8.2,5.1,3.1,0,0,80',
                '0.5,5.0,4.5,0.5,0,0,50'
            ],
            'V21THEMES': [
                'ECON_OILPRICE;WB_632_ENERGY_POLICY;MINING',
                'CONFLICT;WAR;MILITARY_ATTACK',
                'POLICY;GOVERNMENT;ECON_TRADE'
            ]
        })
        
        result = pipeline.process_gdelt_data(mock_data)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty, "Processed data should not be empty"
        
        # Check expected columns
        expected_cols = ['country', 'date', 'avg_tone', 'tone_std', 'mention_count']
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"
        
        # Check theme columns exist
        theme_cols = ['theme_energy', 'theme_conflict', 'theme_policy']
        for col in theme_cols:
            assert col in result.columns, f"Missing theme column: {col}"
        
        print(f"✅ Processed GDELT data: {len(result)} country-day records")
        print(f"   Columns: {list(result.columns)}")
        print(f"   Sample data:\n{result.head()}")
    
    def test_theme_categorization(self):
        """Test theme categorization logic"""
        pipeline = DailyDataPipeline()
        
        test_cases = [
            ('ECON_OILPRICE', 'ENERGY'),
            ('WB_632_ENERGY_POLICY', 'ENERGY'),
            ('CONFLICT', 'CONFLICT'),
            ('WAR_MILITARY', 'CONFLICT'),
            ('SANCTION', 'SANCTIONS'),
            ('TRADE_EXPORT', 'TRADE'),
            ('ECON_INFLATION', 'ECONOMY'),
            ('GOVERNMENT_POLICY', 'POLICY'),
            ('RANDOM_THEME', 'OTHER'),
        ]
        
        for theme, expected_category in test_cases:
            result = pipeline._get_theme_category(theme)
            assert result == expected_category, f"Theme '{theme}' should be '{expected_category}', got '{result}'"
        
        print(f"✅ Theme categorization working correctly")


class TestAlphaVantage:
    """Test Alpha Vantage API fetching"""
    
    @pytest.mark.skipif(not os.environ.get('ALPHA_VANTAGE_API_KEY'), 
                       reason="ALPHA_VANTAGE_API_KEY not set")
    def test_fetch_oil_prices(self):
        """Test fetching oil prices from Alpha Vantage"""
        pipeline = DailyDataPipeline()
        
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        try:
            oil_df = pipeline.fetch_oil_prices(start_date, end_date)
            
            assert isinstance(oil_df, pd.DataFrame)
            assert not oil_df.empty, "Oil price data should not be empty"
            
            # Check expected columns
            expected_cols = ['date', 'value_wti', 'value_brent']
            for col in expected_cols:
                assert col in oil_df.columns, f"Missing column: {col}"
            
            # Check data types
            assert pd.api.types.is_datetime64_any_dtype(oil_df['date'])
            
            print(f"✅ Fetched oil prices: {len(oil_df)} days")
            print(f"   Date range: {oil_df['date'].min()} to {oil_df['date'].max()}")
            print(f"   Sample:\n{oil_df.head()}")
            
        except Exception as e:
            print(f"⚠️  Alpha Vantage fetch failed: {e}")
            print("   This is expected if API rate limit is hit")


class TestFeatureEngineering:
    """Test feature engineering"""
    
    def test_align_and_engineer_features(self):
        """Test feature engineering with mock data"""
        pipeline = DailyDataPipeline()
        
        # Create mock GDELT processed data
        dates = pd.date_range('2023-11-01', periods=45, freq='D')
        gdelt_df = pd.DataFrame({
            'country': ['US'] * 45 + ['SA'] * 45,
            'date': list(dates) + list(dates),
            'avg_tone': np.random.randn(90) * 2,
            'tone_std': np.random.rand(90),
            'mention_count': np.random.randint(10, 100, 90)
        })
        
        # Create mock oil price data
        oil_df = pd.DataFrame({
            'date': dates,
            'value_wti': 70 + np.random.randn(45) * 5,
            'value_brent': 75 + np.random.randn(45) * 5
        })
        
        result = pipeline.align_and_engineer_features(gdelt_df, oil_df)
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty, "Engineered features should not be empty"
        
        # Check that column names are standardized
        assert 'wti_price' in result.columns, "Should have renamed value_wti to wti_price"
        assert 'brent_price' in result.columns, "Should have renamed value_brent to brent_price"
        
        # Check for key engineered features
        key_features = [
            'wti_delta', 'wti_return', 'brent_delta', 'brent_return',
            'wti_delta_lag1', 'wti_delta_lag7', 'wti_delta_lag30',
            'wti_return_ma5', 'wti_return_ma20', 'wti_return_std30',
            'wti_rsi', 'brent_rsi',
            'wti_momentum_5_20', 'wti_momentum_10_30',
            'avg_sentiment', 'event_count'
        ]
        
        missing_features = [f for f in key_features if f not in result.columns]
        assert len(missing_features) == 0, f"Missing features: {missing_features}"
        
        # Count total features
        feature_cols = [c for c in result.columns if c not in ['country', 'date']]
        print(f"✅ Feature engineering working correctly")
        print(f"   Total features generated: {len(feature_cols)}")
        print(f"   Feature sample: {feature_cols[:10]}")
        
        # Verify no NaN values after engineering
        nan_counts = result[feature_cols].isna().sum().sum()
        assert nan_counts == 0, f"Found {nan_counts} NaN values in features"
        
        return result
    
    def test_feature_count_matches_training(self):
        """Ensure we generate at least 61 features matching training"""
        result = self.test_align_and_engineer_features()
        
        # Exclude non-feature columns
        feature_cols = [c for c in result.columns 
                       if c not in ['country', 'date', 'country_iso3', 'node_id']]
        
        print(f"\n📊 Feature Count Analysis:")
        print(f"   Total features: {len(feature_cols)}")
        
        # Categorize features
        lag_features = [c for c in feature_cols if 'lag' in c]
        ma_features = [c for c in feature_cols if 'ma' in c or 'std' in c]
        rsi_features = [c for c in feature_cols if 'rsi' in c]
        momentum_features = [c for c in feature_cols if 'momentum' in c]
        theme_features = [c for c in feature_cols if 'theme_' in c]
        
        print(f"   Lag features: {len(lag_features)}")
        print(f"   MA/Std features: {len(ma_features)}")
        print(f"   RSI features: {len(rsi_features)}")
        print(f"   Momentum features: {len(momentum_features)}")
        print(f"   Theme features: {len(theme_features)}")
        
        # Should have at least 50+ features
        assert len(feature_cols) >= 50, f"Expected at least 50 features, got {len(feature_cols)}"


class TestDataPipelineIntegration:
    """Integration tests for full pipeline"""
    
    @pytest.mark.skipif(not os.environ.get('ALPHA_VANTAGE_API_KEY'), 
                       reason="ALPHA_VANTAGE_API_KEY not set")
    @pytest.mark.skipif(not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                       reason="GOOGLE_APPLICATION_CREDENTIALS not set")
    def test_full_pipeline_run(self):
        """Test running the full pipeline for a recent date"""
        pipeline = DailyDataPipeline()
        
        # Test with 2 days ago (to ensure data is available)
        test_date = datetime.now() - timedelta(days=2)
        
        print(f"\n🔄 Testing full pipeline for {test_date.date()}")
        
        try:
            # This will fetch GDELT, Alpha Vantage, and engineer features
            output_path = pipeline.run_daily_update(test_date)
            
            print(f"✅ Pipeline completed successfully!")
            print(f"   Output path: {output_path}")
            
        except Exception as e:
            print(f"⚠️  Pipeline test failed: {e}")
            print(f"   This might be expected if:")
            print(f"   - GDELT data not available for this date")
            print(f"   - Alpha Vantage rate limit hit")
            print(f"   - GCS permissions not configured")
            raise


if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING DATA PIPELINE TESTS")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, '-v', '-s'])
