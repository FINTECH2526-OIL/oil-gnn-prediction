# Oil GNN Prediction - Testing Guide

## Test Suite Overview

The test suite is organized into three levels:

### 1. Unit Tests (`test_data_pipeline.py`)
Tests individual components of the data pipeline:
- ✅ GDELT data fetching and processing
- ✅ Alpha Vantage API integration
- ✅ Feature engineering (61+ features)
- ✅ Theme categorization
- ✅ Column name standardization

### 2. Inference Tests (`test_inference.py`)
Tests model inference pipeline:
- ✅ Data loading from GCS
- ✅ Feature engineering for inference
- ✅ Model loading (XGBoost + HTG)
- ✅ Prediction generation
- ✅ API response format validation

### 3. End-to-End Tests (`test_e2e.py`)
Tests complete workflow:
- ✅ Data Pipeline → GCS Storage → Inference → Predictions
- ✅ Full integration with real APIs
- ✅ API endpoint testing (if running locally)

## Prerequisites

### Environment Variables

```bash
# Required for Alpha Vantage tests
export ALPHA_VANTAGE_API_KEY="your_api_key"

# Required for GCS tests (path to service account JSON)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Optional: For API endpoint tests
export API_URL="http://localhost:8080"
```

### Install Dependencies

```bash
cd gnn-backend
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
```

## Running Tests

### Quick Start

```bash
# Run all tests
./run_tests.sh all

# Run specific test suite
./run_tests.sh unit        # Unit tests only
./run_tests.sh inference   # Inference tests only
./run_tests.sh e2e         # End-to-end tests only

# Run with coverage
./run_tests.sh coverage

# Verbose output
./run_tests.sh all -v
```

### Manual Testing with pytest

```bash
# Run all tests
pytest tests/ -v -s

# Run specific test file
pytest tests/test_data_pipeline.py -v -s

# Run specific test class
pytest tests/test_inference.py::TestDataLoader -v -s

# Run specific test
pytest tests/test_e2e.py::TestCompleteWorkflow::test_full_workflow -v -s

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Test Details

### Unit Tests (test_data_pipeline.py)

**TestGDELTFetching**
- `test_fetch_single_gdelt_file` - Fetches real GDELT file from yesterday
- `test_process_gdelt_data` - Processes GDELT data with country/theme extraction
- `test_theme_categorization` - Validates theme categorization logic

**TestAlphaVantage**
- `test_fetch_oil_prices` - Fetches WTI/Brent prices from Alpha Vantage API

**TestFeatureEngineering**
- `test_align_and_engineer_features` - Tests complete feature engineering pipeline
- `test_feature_count_matches_training` - Ensures 61+ features are generated

**TestDataPipelineIntegration**
- `test_full_pipeline_run` - Runs complete pipeline for a recent date

### Inference Tests (test_inference.py)

**TestDataLoader**
- `test_load_latest_data_from_gcs` - Loads processed data from GCS bucket
- `test_engineer_features` - Engineers all 61+ features for inference
- `test_prepare_features_for_model` - Prepares feature matrix for model

**TestModelInference**
- `test_load_models` - Loads XGBoost and HTG models from GCS
- `test_predict_single_country` - Makes prediction for one country
- `test_end_to_end_inference` - Full inference workflow

**TestAPICompatibility**
- `test_prediction_format` - Validates API response schema

### E2E Tests (test_e2e.py)

**TestCompleteWorkflow**
- `test_full_workflow` - Complete pipeline:
  1. Run data pipeline for specific date
  2. Verify data saved to GCS
  3. Load data for inference
  4. Engineer features
  5. Make predictions
  6. Validate outputs

**TestAPIEndpoint**
- `test_prediction_endpoint` - Tests `/predict` endpoint
- `test_health_endpoint` - Tests `/health` endpoint

## Expected Output

### Successful Test Run

```
====================================================================
Oil GNN Prediction - Test Suite
====================================================================

✓ ALPHA_VANTAGE_API_KEY is set
✓ GOOGLE_APPLICATION_CREDENTIALS is set

====================================================================
Running Tests: all
====================================================================

1/3: Running Unit Tests (Data Pipeline)
✅ Fetched GDELT file: 10234 records
✅ Processed GDELT data: 45 country-day records
✅ Theme categorization working correctly
✅ Feature engineering working correctly
   Total features generated: 65

2/3: Running Inference Tests
✅ Loaded data from GCS: 1250 records
✅ Feature engineering successful
   Total features: 61
✅ Models loaded successfully
✅ Prediction successful

3/3: Running End-to-End Tests
📊 STEP 1: Running data pipeline
✅ Pipeline completed successfully

💾 STEP 2: Verifying data in GCS
✅ Data loaded from GCS

⚙️  STEP 3: Engineering features
✅ Features engineered
   Total features: 61

🤖 STEP 4: Loading models and making predictions
✅ Predictions completed for 3 countries

====================================================================
✅ All tests passed!
====================================================================
```

## Troubleshooting

### Tests are Skipped

Some tests will be skipped if environment variables are not set:
- Missing `ALPHA_VANTAGE_API_KEY` - Alpha Vantage tests skipped
- Missing `GOOGLE_APPLICATION_CREDENTIALS` - GCS tests skipped
- Missing `API_URL` - API endpoint tests skipped

This is expected behavior for local development.

### Alpha Vantage Rate Limit

If you see rate limit errors:
```
⚠️  Alpha Vantage fetch failed: Rate limit exceeded
```

Wait 1 minute between test runs (free tier limit: 5 API calls/minute).

### GCS Permission Errors

Make sure your service account has:
- `roles/storage.objectAdmin` on the GCS bucket
- Access to `gdelt_raw_3_years` bucket

### Feature Count Mismatch

If tests fail with:
```
AssertionError: Expected at least 50 features, got 13
```

This indicates the feature engineering is incomplete. Check:
1. All lag features are generated (1, 2, 3, 5, 7, 14, 30 days)
2. Moving averages calculated (5, 10, 20, 30 day windows)
3. Theme features included
4. RSI and momentum indicators added

## Coverage Report

Run tests with coverage:
```bash
./run_tests.sh coverage
```

Open `htmlcov/index.html` in browser to view detailed coverage report.

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
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
      - name: Install dependencies
        run: |
          pip install -r gnn-backend/requirements.txt
          pip install -r gnn-backend/tests/requirements-test.txt
      - name: Run tests
        env:
          ALPHA_VANTAGE_API_KEY: ${{ secrets.ALPHA_VANTAGE_API_KEY }}
          GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
        run: |
          cd gnn-backend
          pytest tests/ -v --cov=.
```

## Next Steps

1. **Run Local Tests**: `./run_tests.sh all`
2. **Fix Any Failures**: Review test output and fix issues
3. **Deploy to Staging**: Test with staging environment
4. **Run E2E in Production**: Verify predictions with real data
5. **Monitor**: Set up alerts for test failures

## Questions?

See main documentation:
- `README.md` - Project overview
- `DEPLOYMENT.md` - Deployment guide
- `DATA_PIPELINE.md` - Data pipeline details
- `INFERENCE_PIPELINE_FIXES.md` - Recent bug fixes
