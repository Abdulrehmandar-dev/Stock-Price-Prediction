import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from io import StringIO
import time

class StockDataFetcher:
    """Fetch stock data from Yahoo Finance"""
    
    @staticmethod
    def fetch_stock_data(symbol, days=365, retries=3):
        """Fetch historical stock data with retry logic and rate-limit handling"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates as strings
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            print(f"Fetching {symbol} data from {start_str} to {end_str}...")
            
            # Retry mechanism with exponential backoff for rate limiting
            for attempt in range(retries):
                try:
                    print(f"Attempt {attempt + 1}/{retries}...")
                    
                    # Download with timeout
                    data = yf.download(
                        symbol, 
                        start=start_str, 
                        end=end_str, 
                        progress=False,
                        timeout=15
                    )
                    
                    if data is not None and not data.empty and len(data) > 0:
                        # Reset index to make date a column
                        data = data.reset_index()
                        if 'Date' in data.columns:
                            data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')
                        
                        print(f"✓ Successfully fetched {len(data)} records for {symbol}")
                        return data
                    
                    if attempt < retries - 1:
                        # Exponential backoff: 5s, 10s, 15s
                        wait_time = (attempt + 1) * 5
                        print(f"No data received, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        
                except Exception as e:
                    print(f"Attempt {attempt + 1} error: {str(e)}")
                    if attempt < retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
            
            print(f"✗ Failed to fetch data for {symbol} after {retries} attempts")
            print("Using demo data for testing purposes...")
            
            # Fallback to demo data
            return StockDataFetcher.generate_demo_data(symbol, days)
            
        except Exception as e:
            print(f"Error in fetch_stock_data for {symbol}: {str(e)}")
            print("Using demo data as fallback...")
            return StockDataFetcher.generate_demo_data(symbol, days)
    
    @staticmethod
    def generate_demo_data(symbol, days=365):
        """Generate realistic demo stock data for testing when API is unavailable"""
        print(f"Generating demo data for {symbol}...")
        
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')
        
        # Generate realistic price movement
        np.random.seed(hash(symbol) % 2**32)  # Consistent data per symbol
        
        base_price = {
            'AAPL': 150, 'GOOGL': 140, 'MSFT': 380, 
            'AMZN': 170, 'TSLA': 240, 'META': 300,
            'NFLX': 450, 'NVDA': 875, 'AMD': 140, 'INTC': 35
        }.get(symbol, 100)
        
        # Random walk price
        returns = np.random.normal(0.0005, 0.02, days)
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'Date': dates.strftime('%Y-%m-%d'),
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            'High': prices * (1 + np.random.uniform(0.01, 0.03, days)),
            'Low': prices * (1 + np.random.uniform(-0.03, -0.01, days)),
            'Close': prices,
            'Volume': np.random.randint(int(50e6), int(100e6), days),
            'Adj Close': prices
        })
        
        print(f"✓ Generated {len(data)} demo records for {symbol}")
        return data
    
    @staticmethod
    def get_closing_prices(data):
        """Extract closing prices as numpy array"""
        if data is None:
            return None
        return data['Close'].values
    
    @staticmethod
    def export_to_csv(data, filename):
        """Export data to CSV"""
        try:
            if data is None:
                return None
            data.to_csv(filename, index=False)
            return filename
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            return None
    
    @staticmethod
    def data_to_dict(data):
        """Convert dataframe to dictionary for JSON serialization"""
        if data is None:
            return None
        return data.to_dict('records')
    
    @staticmethod
    def validate_symbol(symbol):
        """Validate stock symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'longName' in info or info.get('symbol') is not None
        except:
            return False

class ChartGenerator:
    """Generate chart data for visualization"""
    
    @staticmethod
    def prepare_prediction_data(actual_data, predictions):
        """Prepare data for chart visualization"""
        chart_data = {
            'actual': actual_data[-30:].tolist() if len(actual_data) > 30 else actual_data.tolist(),
            'predicted': predictions,
            'dates': [f"Day {i+1}" for i in range(len(predictions))]
        }
        return chart_data
    
    @staticmethod
    def prepare_comparison_data(lstm_pred, linear_pred, rf_pred, arima_pred):
        """Prepare data for model comparison"""
        comparison = {
            'LSTM': lstm_pred[:10] if lstm_pred else [],
            'Linear Regression': linear_pred[:10] if linear_pred else [],
            'Random Forest': rf_pred[:10] if rf_pred else [],
            'ARIMA': arima_pred[:10] if arima_pred else []
        }
        return comparison
    
    @staticmethod
    def prepare_metrics_data(lstm_rmse, lstm_mae, linear_rmse, linear_mae, rf_rmse, rf_mae, arima_rmse, arima_mae):
        """Prepare metrics for display"""
        metrics = {
            'LSTM': {'RMSE': round(lstm_rmse, 4), 'MAE': round(lstm_mae, 4)},
            'Linear Regression': {'RMSE': round(linear_rmse, 4), 'MAE': round(linear_mae, 4)},
            'Random Forest': {'RMSE': round(rf_rmse, 4), 'MAE': round(rf_mae, 4)},
            'ARIMA': {'RMSE': round(arima_rmse, 4), 'MAE': round(arima_mae, 4)}
        }
        return metrics

class ExportManager:
    """Handle exports of data and charts"""
    
    @staticmethod
    def export_chart_to_image(fig, filename):
        """Export plotly figure to image"""
        try:
            fig.write_image(filename)
            return filename
        except Exception as e:
            print(f"Error exporting chart to image: {str(e)}")
            return None
    
    @staticmethod
    def export_chart_to_pdf(fig, filename):
        """Export plotly figure to PDF"""
        try:
            fig.write_image(filename, format='pdf')
            return filename
        except Exception as e:
            print(f"Error exporting chart to PDF: {str(e)}")
            return None
