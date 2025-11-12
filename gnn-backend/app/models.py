"""Model class definitions required for unpickling trained models"""
import xgboost as xgb
from sklearn.preprocessing import RobustScaler


class CountryTemporalModels:
    """Container for country-specific and global temporal models"""
    def __init__(self, key_countries=None):
        self.key_countries = key_countries or []
        self.country_models = {}
        self.country_scalers = {}
        self.global_model = None
        self.global_scaler = None
    
    def predict_all_countries(self, df_test, feature_cols):
        """Predict for all countries on test data"""
        predictions = {}
        for date in df_test['date'].unique():
            date_data = df_test[df_test['date'] == date]
            date_predictions = {}
            
            X_global = date_data[feature_cols].fillna(0).values
            if len(X_global) > 0:
                X_global_scaled = self.global_scaler.transform(X_global)
                global_pred = self.global_model.predict(X_global_scaled).mean()
            else:
                global_pred = 0
            
            for country in self.key_countries:
                if country in self.country_models:
                    country_data = date_data[date_data['country_iso3'] == country]
                    if len(country_data) > 0:
                        X_country = country_data[feature_cols].fillna(0).values
                        X_scaled = self.country_scalers[country].transform(X_country)
                        pred = self.country_models[country].predict(X_scaled)[0]
                        date_predictions[country] = pred
                    else:
                        date_predictions[country] = global_pred
                else:
                    date_predictions[country] = global_pred
            
            predictions[date] = date_predictions
        
        return predictions
