# Testing Quick Start Guide

## 🚀 Quick Start (30 seconds)

```bash
cd gnn-backend

# 1. Quick verification
python3 tests/quick_check.py

# 2. Run all tests
./run_tests.sh all
```

## 📋 What Gets Tested

### ✅ Data Pipeline Tests
- Fetching GDELT data (96 files/day)
- Fetching oil prices from Alpha Vantage
- Processing and aggregating by country
- **Feature engineering: 13 → 61+ features** ⭐
- Theme extraction and categorization
- Column name standardization

### ✅ Inference Tests  
- Loading data from GCS bucket
- Feature engineering matches training exactly
- Model loading (XGBoost + HTG)
- Making predictions
- API response format

### ✅ End-to-End Tests
- Complete workflow from data fetch to prediction
- Real API integration
- GCS storage verification
- Prediction validation

## 🔧 Setup (First Time Only)

```bash
# Set environment variables
export ALPHA_VANTAGE_API_KEY="your_key_here"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Install test dependencies
pip install -r tests/requirements-test.txt
```

## 🎯 Running Tests

```bash
# Run everything (recommended)
./run_tests.sh all

# Run specific test suites
./run_tests.sh unit        # Data pipeline only
./run_tests.sh inference   # Inference only  
./run_tests.sh e2e         # End-to-end only

# With coverage report
./run_tests.sh coverage    # Opens htmlcov/index.html

# Verbose output
./run_tests.sh all -v
```

## 📊 Expected Output

```
====================================================================
Oil GNN Prediction - Test Suite
====================================================================

✓ ALPHA_VANTAGE_API_KEY is set
✓ GOOGLE_APPLICATION_CREDENTIALS is set

Running Tests: all
====================================================================

1/3: Running Unit Tests
✅ Fetched GDELT file: 10234 records
✅ Processed GDELT data: 45 country-day records  
✅ Feature engineering working correctly
   Total features generated: 61

2/3: Running Inference Tests
✅ Loaded data from GCS: 1250 records
✅ Features engineered: 61 features
✅ Models loaded successfully
✅ Predictions completed

3/3: Running End-to-End Tests
📊 Running full pipeline for 2024-11-09
✅ Pipeline completed successfully
✅ Data verified in GCS
✅ Predictions: US: 2.8%, SA: -1.2%, IQ: 1.5%

====================================================================
✅ All tests passed!
====================================================================
```

## 🐛 Troubleshooting

### Missing Environment Variables
```
⚠️  ALPHA_VANTAGE_API_KEY not set
   Some tests will be skipped
```
**Fix**: Set the environment variable (see Setup above)

### Alpha Vantage Rate Limit
```
⚠️  Alpha Vantage fetch failed: Rate limit exceeded
```
**Fix**: Wait 1 minute between test runs (free tier: 5 calls/min)

### GCS Permission Error
```
❌ Failed to load data: 403 Forbidden
```
**Fix**: Check service account has `roles/storage.objectAdmin`

### Feature Count Too Low
```
AssertionError: Expected at least 50 features, got 13
```
**Fix**: This shouldn't happen after commit cab907d. If it does, re-check feature engineering code.

## 📝 What the Tests Verify

### Critical Bug Fixes (from commit cab907d)
- ✅ Column name bug fixed: `country_code` → `country`  
- ✅ Oil price columns standardized: `value_wti` → `wti_price`
- ✅ All 61+ features generated (was only 13 before)
- ✅ Theme processing working correctly
- ✅ No NaN values in feature matrix
- ✅ Backward compatible with old column names

### Production Readiness
- ✅ Real API integration works
- ✅ GCS storage/retrieval works
- ✅ Models can be loaded
- ✅ Predictions are valid (-100% to +100%)
- ✅ No data type errors
- ✅ No shape mismatches

## 🎓 Test Organization

```
gnn-backend/tests/
├── __init__.py
├── README.md                    # Detailed testing guide
├── requirements-test.txt        # Test dependencies
├── quick_check.py              # Pre-test verification
├── test_data_pipeline.py       # Unit tests (pipeline)
├── test_inference.py           # Unit tests (inference)
└── test_e2e.py                 # Integration tests
```

## 🔄 CI/CD Integration

To add to GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run tests
        env:
          ALPHA_VANTAGE_API_KEY: ${{ secrets.ALPHA_VANTAGE_API_KEY }}
        run: |
          cd gnn-backend
          ./run_tests.sh all
```

## 📚 Documentation

- `tests/README.md` - Complete testing guide
- `INFERENCE_PIPELINE_FIXES.md` - Bug fixes that these tests verify
- `DATA_PIPELINE.md` - Data pipeline documentation

## ✅ Next Steps

1. **Run locally**: `./run_tests.sh all`
2. **Fix any failures**: Review output and fix issues  
3. **Deploy to staging**: Test in cloud environment
4. **Monitor production**: Set up alerts for failures
5. **Add to CI/CD**: Automate testing on every commit

---

**Questions?** See `tests/README.md` for detailed documentation.
