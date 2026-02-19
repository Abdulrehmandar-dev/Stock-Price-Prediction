#!/usr/bin/env python3
"""
Stock Price Prediction Application - Main Entry Point

This script starts the Flask web application.
"""

import os
import sys

# Add current directory to path to import properly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db

def main():
    """Run the application"""
    # Ensure data directories exist
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/downloads', exist_ok=True)
    
    # Initialize database
    init_db()
    
    print("\n" + "="*50)
    print("🚀 Stock Price Prediction Application")
    print("="*50)
    print("🌐 Server running at: http://localhost:5000")
    print("📊 Open your browser and start predicting!")
    print("⏸️  Press CTRL+C to stop")
    print("="*50 + "\n")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )

if __name__ == "__main__":
    main()
