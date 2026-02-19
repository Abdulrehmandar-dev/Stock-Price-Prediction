import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings('ignore')

class StockPredictionModels:
    """Class to handle all prediction models"""
    
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.results = {}
    
    def prepare_data(self, data, lookback=60):
        """Prepare data for LSTM"""
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))
        
        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, input_shape):
        """Build LSTM model"""
        model = Sequential([
            LSTM(50, activation='relu', return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, activation='relu', return_sequences=True),
            Dropout(0.2),
            LSTM(25, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def predict_lstm(self, data, days_to_predict=30):
        """LSTM prediction"""
        lookback = 60
        X, y = self.prepare_data(data, lookback)
        
        if len(X) < 10:
            return None, None, None
        
        # Split data (80-20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Reshape for LSTM
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
        
        # Build and train
        model = self.build_lstm_model((lookback, 1))
        early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
        model.fit(X_train, y_train, epochs=50, batch_size=32, callbacks=[early_stop], verbose=0)
        
        # Predict on test set
        train_predict = model.predict(X_train, verbose=0)
        test_predict = model.predict(X_test, verbose=0)
        
        # Inverse transform
        train_predict = self.scaler.inverse_transform(train_predict)
        test_predict = self.scaler.inverse_transform(test_predict)
        y_test_actual = self.scaler.inverse_transform(y_test.reshape(-1, 1))
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y_test_actual, test_predict))
        mae = mean_absolute_error(y_test_actual, test_predict)
        
        # Future predictions
        last_sequence = X[-1]
        future_predictions = []
        
        for _ in range(days_to_predict):
            next_input = last_sequence.reshape((1, lookback, 1))
            next_pred = model.predict(next_input, verbose=0)[0, 0]
            future_predictions.append(self.scaler.inverse_transform([[next_pred]])[0, 0])
            last_sequence = np.append(last_sequence[1:], next_pred)
        
        return future_predictions, rmse, mae
    
    def predict_linear_regression(self, data, days_to_predict=30):
        """Linear Regression prediction"""
        X = np.arange(len(data)).reshape(-1, 1)
        y = data
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        # Future predictions
        future_X = np.arange(len(data), len(data) + days_to_predict).reshape(-1, 1)
        future_predictions = model.predict(future_X).tolist()
        
        return future_predictions, rmse, mae
    
    def predict_random_forest(self, data, days_to_predict=30):
        """Random Forest prediction"""
        lookback = 10
        X, y = [], []
        
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i])
            y.append(data[i])
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 10:
            return None, None, None
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        # Future predictions
        last_sequence = data[-lookback:]
        future_predictions = []
        
        for _ in range(days_to_predict):
            next_pred = model.predict([last_sequence])[0]
            future_predictions.append(next_pred)
            last_sequence = np.append(last_sequence[1:], next_pred)
        
        return future_predictions, rmse, mae
    
    def predict_arima_simple(self, data, days_to_predict=30):
        """Simple ARIMA-like prediction using exponential smoothing"""
        # Simple exponential smoothing
        alpha = 0.3
        result = [data[0]]
        
        for i in range(1, len(data)):
            result.append(alpha * data[i] + (1 - alpha) * result[i-1])
        
        # Split data
        split_idx = int(len(data) * 0.8)
        y_test = data[split_idx:]
        y_pred = result[split_idx:]
        
        # Metrics
        rmse = np.sqrt(mean_squared_error(y_test, y_pred[:len(y_test)]))
        mae = mean_absolute_error(y_test, y_pred[:len(y_test)])
        
        # Future predictions
        future_predictions = []
        last_value = result[-1]
        
        for _ in range(days_to_predict):
            next_pred = alpha * data[-1] + (1 - alpha) * last_value
            future_predictions.append(next_pred)
            last_value = next_pred
        
        return future_predictions, rmse, mae
    
    def predict_all_models(self, data, days_to_predict=30):
        """Run all prediction models"""
        results = {
            'lstm': self.predict_lstm(data, days_to_predict),
            'linear': self.predict_linear_regression(data, days_to_predict),
            'random_forest': self.predict_random_forest(data, days_to_predict),
            'arima': self.predict_arima_simple(data, days_to_predict),
        }
        
        return results
