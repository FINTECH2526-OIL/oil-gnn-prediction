# Inference Pipeline Fix Plan

## Problem Identified
The inference pipeline has several mismatches with the training data format:

### 1. **Data Schema Mismatch**
**Training data format** (from `data_engineering.py`):
```python
{
    'date': '20221201',  # YYYYMMDD format
    'country': 'US',  # 2-letter ISO code
    'event_count': 150,
    'avg_sentiment': 0.25,
    'unique_sources': 45,
    'wti_price': 82.50,
    'brent_price': 88.20,
    'theme_energy': 20,
    'theme_conflict': 5,
    'theme_sanctions': 2,
    'theme_trade': 10,
    'theme_economy': 15,
    'theme_policy': 8
}
```

**Bug in `daily_data_pipeline_standalone.py` line 168**:
```python
merged = merged.sort_values(['country_code', 'date'])  # ❌ WRONG - uses 'country_code'
```
Should be:
```python
merged = merged.sort_values(['country', 'date'])  # ✅ CORRECT
```

### 2. **Missing Feature Engineering**
The `daily_data_pipeline_standalone.py` creates only **13 features**, but training expects **61 features** after VIF selection.

**Current features** (13):
- value_wti_lag1, value_wti_lag7, value_wti_return, value_wti_ma7, value_wti_ma30
- value_brent_lag1, value_brent_lag7, value_brent_return, value_brent_ma7, value_brent_ma30
- tone_lag1, tone_lag7, mention_count_lag1

**Missing features** from training:
- All theme-based features (theme_energy, theme_conflict, etc.)
- Sentiment/tone features (avg_sentiment, tone_std)
- Event count features  
- Source diversity features
- Price volatility features (std, RSI)
- Additional lag windows (2, 3, 5, 14, 30 days)

### 3. **Column Name Inconsistencies**
- Training uses: `wti_price`, `brent_price`
- Daily pipeline uses: `value_wti`, `value_brent`
- Must standardize to training format

## Solution

### Fix 1: Correct `daily_data_pipeline_standalone.py`
```python
def align_and_engineer_features(self, gdelt_df: pd.DataFrame, oil_df: pd.DataFrame) -> pd.DataFrame:
    """Align GDELT and oil price data, engineer features matching training format"""
    gdelt_df['date'] = pd.to_datetime(gdelt_df['date'])
    oil_df['date'] = pd.to_datetime(oil_df['date'])
    
    # Rename oil columns to match training format
    oil_df = oil_df.rename(columns={
        'value_wti': 'wti_price',
        'value_brent': 'brent_price'
    })
    
    # Merge with oil prices
    merged = pd.merge(gdelt_df, oil_df, on='date', how='inner')
    
    # Convert oil prices to numeric
    for col in ['wti_price', 'brent_price']:
        merged[col] = pd.to_numeric(merged[col], errors='coerce')
    
    # ✅ FIX: Use 'country' not 'country_code'
    merged = merged.sort_values(['country', 'date']).reset_index(drop=True)
    
    # ... rest of feature engineering
```

### Fix 2: Add Missing Features to Pipeline
The daily pipeline must output the same format as training data includes theme columns.

### Fix 3: Update `data_loader.py` 
Ensure it handles both column naming conventions and applies exact same feature engineering as training.

## Files to Update
1. ✅ `gnn-backend/daily_data_pipeline_standalone.py` - Fix column names, add theme processing
2. ✅ `gnn-backend/app/data_loader.py` - Match training feature engineering exactly  
3. ✅ `gnn-backend/app/daily_data_pipeline.py` - Sync with standalone version
4. ✅ `gnn-backend/app/inference.py` - Handle flexible column naming

## Expected Feature Count
After fixes, inference should have same 61 features as training (post-VIF):
- Base features: ~13 (GDELT + oil price)
- Theme features: ~6 (energy, conflict, sanctions, trade, economy, policy)  
- Engineered features: ~42 (lags, MAs, stds, returns, RSI, momentum)
- **Total: ~61 features**
