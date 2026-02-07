#!/usr/bin/env python3
"""
Quick test script to verify data pipeline and inference setup
Run this before the full test suite to check basic functionality
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_imports():
    """Check if all required packages can be imported"""
    print(" Checking package imports...")
    
    required_packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('google.cloud.storage', 'google-cloud-storage'),
    ]
    
    missing = []
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"   {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT FOUND")
            missing.append(package)
    
    if missing:
        print(f"\n Missing packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False
    
    print(" All required packages available\n")
    return True


def check_environment():
    """Check environment variables"""
    print(" Checking environment variables...")
    
    env_vars = {
        'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage API access',
        'GOOGLE_APPLICATION_CREDENTIALS': 'GCS access',
    }
    
    all_set = True
    for var, description in env_vars.items():
        if os.environ.get(var):
            print(f"   {var}")
        else:
            print(f"  ️  {var} - NOT SET ({description})")
            all_set = False
    
    if not all_set:
        print("\n️  Some environment variables not set")
        print("   Some tests will be skipped\n")
    else:
        print(" All environment variables set\n")
    
    return True


def check_modules():
    """Check if our modules can be imported"""
    print(" Checking project modules...")
    
    try:
        from daily_data_pipeline_standalone import DailyDataPipeline
        print("   daily_data_pipeline_standalone")
    except ImportError as e:
        print(f"  ✗ daily_data_pipeline_standalone - {e}")
        return False
    
    try:
        from app.data_loader import DataLoader
        print("   app.data_loader")
    except ImportError as e:
        print(f"  ✗ app.data_loader - {e}")
        return False
    
    try:
        from app.inference import ModelInference
        print("   app.inference")
    except ImportError as e:
        print(f"  ✗ app.inference - {e}")
        return False
    
    print(" All project modules can be imported\n")
    return True


def test_feature_engineering():
    """Quick test of feature engineering"""
    print(" Testing feature engineering...")
    
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        from app.data_loader import DataLoader
        
        # Create minimal mock data
        dates = pd.date_range('2023-11-01', periods=45, freq='D')
        mock_df = pd.DataFrame({
            'country': ['US'] * 45,
            'date': dates,
            'wti_price': 70 + np.random.randn(45) * 2,
            'brent_price': 75 + np.random.randn(45) * 2,
            'avg_tone': np.random.randn(45),
            'tone_std': np.random.rand(45),
            'mention_count': np.random.randint(10, 100, 45),
            'theme_energy': np.random.randint(0, 20, 45),
            'theme_conflict': np.random.randint(0, 15, 45),
            'theme_sanctions': np.random.randint(0, 10, 45),
            'theme_trade': np.random.randint(0, 12, 45),
            'theme_economy': np.random.randint(0, 25, 45),
            'theme_policy': np.random.randint(0, 18, 45),
        })
        
        loader = DataLoader()
        result = loader.engineer_features(mock_df)
        
        feature_cols = [c for c in result.columns 
                       if c not in ['country', 'date', 'country_iso3', 'node_id']]
        
        print(f"  Features generated: {len(feature_cols)}")
        
        if len(feature_cols) >= 50:
            print(f"   Feature count OK (≥50)")
        else:
            print(f"  ️  Feature count low (expected ≥50, got {len(feature_cols)})")
        
        # Check for NaN
        nan_count = result[feature_cols].isna().sum().sum()
        if nan_count == 0:
            print(f"   No NaN values")
        else:
            print(f"  ️  Found {nan_count} NaN values")
        
        print(" Feature engineering test passed\n")
        return True
        
    except Exception as e:
        print(f" Feature engineering test failed: {e}\n")
        return False


def main():
    """Run all quick checks"""
    print("="*70)
    print("Quick Setup Verification")
    print("="*70)
    print()
    
    checks = [
        check_imports(),
        check_environment(),
        check_modules(),
        test_feature_engineering(),
    ]
    
    print("="*70)
    if all(checks):
        print(" All checks passed! Ready to run full test suite.")
        print()
        print("Run full tests with:")
        print("  ./run_tests.sh all")
        print("="*70)
        return 0
    else:
        print("️  Some checks failed. Fix issues before running tests.")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
