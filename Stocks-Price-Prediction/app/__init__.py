from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
import json
from datetime import datetime
from config import config
from models import db, User, Prediction, StockData, FAQItem
from utils.data_utils import StockDataFetcher, ChartGenerator, ExportManager
from utils.prediction_models import StockPredictionModels
from utils.chatbot import StockChatbot

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object(config['development'])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize utilities
chatbot = StockChatbot()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== CONTEXT PROCESSORS ====================
@app.context_processor
def inject_user():
    """Inject user data into all templates"""
    return dict(current_user=current_user)

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ==================== AUTHENTICATION ROUTES ====================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        
        if not email or '@' not in email:
            errors.append('Invalid email address')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check existing user
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful! Please log in.'}), 201
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Check by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)
            user.update_last_login()
            return jsonify({'success': True, 'message': 'Login successful!'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'Email not found'}), 404
        
        # TODO: Send reset email
        return jsonify({'success': True, 'message': 'Password reset link sent to email'}), 200
    
    return render_template('forgot_password.html')

# ==================== MAIN ROUTES ====================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    last_prediction = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).first()
    predictions_count = Prediction.query.filter_by(user_id=current_user.id).count()
    
    return render_template('dashboard.html', 
                         username=current_user.username,
                         predictions_count=predictions_count,
                         last_prediction=last_prediction.stock_symbol if last_prediction else None)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/faqs')
@login_required
def faqs():
    faq_items = FAQItem.query.all()
    return render_template('faqs.html', faqs=faq_items)

# ==================== PREDICTION ROUTES ====================
@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction():
    if request.method == 'GET':
        return render_template('prediction.html')
    
    # POST request for prediction
    data = request.get_json()
    stock_symbol = data.get('symbol', '').upper()
    days_to_predict = int(data.get('days', 30))
    
    # Validation
    if not stock_symbol:
        return jsonify({'success': False, 'message': 'Stock symbol is required'}), 400
    
    if days_to_predict < 1 or days_to_predict > 30:
        return jsonify({'success': False, 'message': 'Days must be between 1 and 30'}), 400
    
    try:
        # Fetch stock data with retry
        stock_data = StockDataFetcher.fetch_stock_data(stock_symbol, days=365, retries=3)
        
        if stock_data is None or stock_data.empty:
            return jsonify({'success': False, 'message': f'Unable to fetch data for {stock_symbol}. Please check the symbol and try again.'}), 400
        
        # Get closing prices
        closing_prices = StockDataFetcher.get_closing_prices(stock_data)
        
        if closing_prices is None or len(closing_prices) < 60:
            return jsonify({'success': False, 'message': f'Insufficient data for {stock_symbol}. Need at least 60 days of data.'}), 400
        
        # Run predictions
        model = StockPredictionModels()
        results = model.predict_all_models(closing_prices, days_to_predict)
        
        # Extract results
        lstm_pred, lstm_rmse, lstm_mae = results['lstm']
        linear_pred, linear_rmse, linear_mae = results['linear']
        rf_pred, rf_rmse, rf_mae = results['random_forest']
        arima_pred, arima_rmse, arima_mae = results['arima']
        
        # Prepare chart data
        chart_data = ChartGenerator.prepare_prediction_data(closing_prices, lstm_pred if lstm_pred else linear_pred)
        comparison_data = ChartGenerator.prepare_comparison_data(lstm_pred, linear_pred, rf_pred, arima_pred)
        metrics_data = ChartGenerator.prepare_metrics_data(lstm_rmse, lstm_mae, linear_rmse, linear_mae, rf_rmse, rf_mae, arima_rmse, arima_mae)
        
        # Helper to convert numpy arrays or lists to plain Python lists
        def _to_list(x):
            if x is None:
                return []
            if hasattr(x, 'tolist'):
                try:
                    return x.tolist()
                except Exception:
                    pass
            return list(x)

        # Save to database
        prediction = Prediction(
            user_id=current_user.id,
            stock_symbol=stock_symbol,
            days_to_predict=days_to_predict,
            lstm_predictions=json.dumps(_to_list(lstm_pred)),
            linear_predictions=json.dumps(_to_list(linear_pred)),
            rf_predictions=json.dumps(_to_list(rf_pred)),
            arima_predictions=json.dumps(_to_list(arima_pred)),
            lstm_rmse=lstm_rmse,
            lstm_mae=lstm_mae,
            linear_rmse=linear_rmse,
            linear_mae=linear_mae,
            rf_rmse=rf_rmse,
            rf_mae=rf_mae,
            arima_rmse=arima_rmse,
            arima_mae=arima_mae,
            chart_data=json.dumps(chart_data)
        )
        db.session.add(prediction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'predictions': {
                'lstm': _to_list(lstm_pred),
                'linear': _to_list(linear_pred),
                'random_forest': _to_list(rf_pred),
                'arima': _to_list(arima_pred)
            },
            'metrics': metrics_data,
            'comparison': comparison_data,
            'current_price': float(closing_prices[-1])
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== DATA ROUTES ====================
@app.route('/download-data', methods=['GET', 'POST'])
@login_required
def download_data():
    if request.method == 'GET':
        return render_template('download_data.html')
    
    data = request.get_json()
    stock_symbol = data.get('symbol', '').upper()
    days = int(data.get('days', 365))
    
    try:
        # Fetch data
        stock_data = StockDataFetcher.fetch_stock_data(stock_symbol, days=days)
        
        if stock_data is None or stock_data.empty:
            return jsonify({'success': False, 'message': f'Stock symbol {stock_symbol} not found'}), 404
        
        # Save to cache
        cache = StockData(
            stock_symbol=stock_symbol,
            data=json.dumps(StockDataFetcher.data_to_dict(stock_data))
        )
        db.session.merge(cache)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': StockDataFetcher.data_to_dict(stock_data),
            'message': f'Data for {stock_symbol} retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/export-csv/<stock_symbol>')
@login_required
def export_csv(stock_symbol):
    try:
        stock_data = StockDataFetcher.fetch_stock_data(stock_symbol, days=365)
        
        if stock_data is None:
            return jsonify({'success': False, 'message': 'Stock not found'}), 404
        
        # Export to CSV
        filename = f"data/downloads/{stock_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        StockDataFetcher.export_to_csv(stock_data, filename)
        
        return send_file(filename, as_attachment=True, download_name=f"{stock_symbol}_data.csv")
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== CHATBOT ROUTES ====================
@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'success': False, 'message': 'Empty message'}), 400
    
    response = chatbot.get_response(user_message)
    
    return jsonify({
        'success': True,
        'response': response
    }), 200

@app.route('/chat-tips')
@login_required
def chat_tips():
    tips = chatbot.get_quick_tips()
    return jsonify({'tips': tips}), 200

# ==================== API ROUTES ====================
@app.route('/api/stock-symbols')
@login_required
def get_stock_symbols():
    symbols = app.config['STOCK_SYMBOLS']
    return jsonify({'symbols': symbols}), 200

@app.route('/api/prediction-history')
@login_required
def get_prediction_history():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(10).all()
    
    data = [{
        'id': p.id,
        'stock_symbol': p.stock_symbol,
        'days': p.days_to_predict,
        'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for p in predictions]
    
    return jsonify(data), 200

# ==================== INITIALIZATION ====================
def init_db():
    """Initialize database with sample FAQs"""
    with app.app_context():
        db.create_all()
        
        # Add sample FAQs if not exist
        if FAQItem.query.count() == 0:
            faqs = [
                FAQItem(question="What is LSTM?", answer="LSTM (Long Short-Term Memory) is a type of recurrent neural network that can learn long-term dependencies in time series data.", category="Models"),
                FAQItem(question="How accurate are the predictions?", answer="Accuracy depends on historical data and market conditions. Compare RMSE and MAE metrics across models for best results.", category="Predictions"),
                FAQItem(question="Can I download my data?", answer="Yes! Use the 'Download Stock Data' feature to export historical data as CSV.", category="Features"),
                FAQItem(question="What stock symbols are available?", answer="We support AAPL, GOOGL, MSFT, AMZN, TSLA, META, NFLX, NVDA, AMD, INTC and more.", category="Data"),
                FAQItem(question="How do I reset my password?", answer="Click 'Forgot Password' on the login page and follow the email instructions.", category="Account"),
            ]
            for faq in faqs:
                db.session.add(faq)
            db.session.commit()
