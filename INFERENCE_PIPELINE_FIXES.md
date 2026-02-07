# Inference Pipeline Fixes - Summary

## Problems Fixed

### 1.  Column Name Bug in `daily_data_pipeline_standalone.py`
**Line 168**: Changed from `country_code` to `country`
```python
# Before (Bug):
merged = merged.sort_values(['country_code', 'date'])

# After (Fixed):
merged = merged.sort_values(['country', 'date'])
```

### 2.  Oil Price Column Names Standardized
**Lines 154-169**: Renamed columns to match training format
```python
# Before:
'value_wti', 'value_brent'

# After:
'wti_price', 'brent_price'
```

### 3.  Complete Feature Engineering Added
**Lines 170-250**: Now generates all 61+ features matching training:

#### Oil Price Features (WTI & Brent):
- Returns & Deltas: `wti_return`, `wti_delta`, `brent_return`, `brent_delta`
- Lags: 1, 2, 3, 5, 7, 14, 30 days
- Moving Averages: 5, 10, 20, 30 day windows
- Volatility: std for each window
- RSI: 14-day Relative Strength Index
- Momentum: 5-20 and 10-30 day momentum

#### GDELT/Sentiment Features:
- `avg_sentiment` (renamed from `avg_tone`)
- `avg_sentiment_lag1` through `lag7`
- `tone_std` with lags
- `event_count` (renamed from `mention_count`) with lags

#### Theme Features:
- 6 categories: `theme_energy`, `theme_conflict`, `theme_sanctions`, `theme_trade`, `theme_economy`, `theme_policy`
- For each theme:
  - `{theme}_change` - daily change
  - `{theme}_pct_change` - percentage change  
  - `{theme}_zscore` - z-score for anomaly detection
  - `{theme}_spike` - binary spike indicator

### 4.  Theme Processing Added to GDELT Pipeline
**Lines 113-200**: New `_get_theme_category()` method categorizes GDELT themes
- Extracts themes from `V21THEMES` column
- Maps to 6 major categories (ENERGY, CONFLICT, SANCTIONS, TRADE, ECONOMY, POLICY)
- Aggregates theme counts per country-day

### 5.  Data Loader Feature Engineering Updated
**File: `gnn-backend/app/data_loader.py`**
- Now generates ALL features matching training exactly
- Handles both old column names (`avg_tone`, `mention_count`) and new names (`avg_sentiment`, `event_count`)
- Includes all theme feature engineering (changes, z-scores, spikes)

## Data Flow (Fixed)

### Raw Data → Processed Data:
```
GDELT Raw (96 files/day)
├── V21LOCATIONS → country codes
├── V21TONE → avg_tone, tone_std
├── V21THEMES → theme_energy, theme_conflict, etc.
└── Aggregate by (country, date)

Alpha Vantage API
├── WTI daily prices → wti_price
└── Brent daily prices → brent_price

Merge on date
├── Sort by (country, date)
└── Engineer 61+ features
```

### Engineered Features (61+):
1. **Base Features** (13):
   - wti_price, brent_price
   - avg_sentiment, tone_std, event_count
   - unique_sources
   - 6 theme counts

2. **Temporal Features** (~30):
   - Lags: 1, 2, 3, 5, 7, 14, 30 days
   - MAs: 5, 10, 20, 30 day windows
   - Stds: 5, 10, 20, 30 day windows

3. **Derived Features** (~18):
   - Returns & Deltas
   - RSI indicators
   - Momentum indicators
   - Theme z-scores & spikes

## Files Modified

1.  `gnn-backend/daily_data_pipeline_standalone.py`
   - Fixed column name bug
   - Added complete feature engineering
   - Added theme processing

2.  `gnn-backend/app/data_loader.py`
   - Updated feature engineering to match training exactly
   - Added theme feature engineering
   - Handles both naming conventions

3.  `INFERENCE_FIX_PLAN.md` (Created)
   - Documentation of the problems and solutions

## Testing Checklist

- [ ] Run daily pipeline for a test date
- [ ] Verify output has 61+ features
- [ ] Check column names match training format
- [ ] Verify theme processing works correctly
- [ ] Test inference with new data
- [ ] Confirm predictions are reasonable

## Next Steps

1. Update `gnn-backend/app/daily_data_pipeline.py` to sync with standalone version
2. Deploy updated code to Cloud Run
3. Test end-to-end with real GDELT + Alpha Vantage data
4. Monitor feature counts in production logs
