from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# SQLAlchemy instance
db = SQLAlchemy()


class User(UserMixin, db.Model):
	"""User model for authentication"""
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False, index=True)
	email = db.Column(db.String(120), unique=True, nullable=False, index=True)
	password_hash = db.Column(db.String(255), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	last_login = db.Column(db.DateTime)
	is_active = db.Column(db.Boolean, default=True)
    
	# Relationships
	predictions = db.relationship('Prediction', backref='user', lazy=True, cascade='all, delete-orphan')
    
	def set_password(self, password):
		"""Hash and set password"""
		self.password_hash = generate_password_hash(password)
    
	def check_password(self, password):
		"""Verify password"""
		return check_password_hash(self.password_hash, password)
    
	def update_last_login(self):
		"""Update last login timestamp"""
		self.last_login = datetime.utcnow()
		db.session.commit()

class Prediction(db.Model):
	"""Model to store prediction history"""
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	stock_symbol = db.Column(db.String(10), nullable=False)
	days_to_predict = db.Column(db.Integer, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
	# Prediction results (as JSON strings)
	lstm_predictions = db.Column(db.Text)  # JSON
	linear_predictions = db.Column(db.Text)  # JSON
	rf_predictions = db.Column(db.Text)  # JSON
	arima_predictions = db.Column(db.Text)  # JSON
    
	# Metrics
	lstm_rmse = db.Column(db.Float)
	lstm_mae = db.Column(db.Float)
	linear_rmse = db.Column(db.Float)
	linear_mae = db.Column(db.Float)
	rf_rmse = db.Column(db.Float)
	rf_mae = db.Column(db.Float)
	arima_rmse = db.Column(db.Float)
	arima_mae = db.Column(db.Float)
    
	# Chart data
	chart_data = db.Column(db.Text)  # JSON
    
	def to_dict(self):
		return {
			'id': self.id,
			'stock_symbol': self.stock_symbol,
			'days_to_predict': self.days_to_predict,
			'created_at': self.created_at.isoformat(),
		}

class StockData(db.Model):
	"""Cache for downloaded stock data"""
	id = db.Column(db.Integer, primary_key=True)
	stock_symbol = db.Column(db.String(10), nullable=False, unique=True, index=True)
	data = db.Column(db.Text, nullable=False)  # JSON
	last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
class FAQItem(db.Model):
	"""FAQ items"""
	id = db.Column(db.Integer, primary_key=True)
	question = db.Column(db.String(255), nullable=False)
	answer = db.Column(db.Text, nullable=False)
	category = db.Column(db.String(50), default='General')
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
