import json
import re

class StockChatbot:
    """Simple chatbot for stock-related queries"""
    
    def __init__(self):
        self.responses = self._initialize_responses()
    
    def _initialize_responses(self):
        """Initialize chatbot responses"""
        return {
            'greeting': {
                'keywords': ['hello', 'hi', 'hey', 'greetings'],
                'response': "Hello! Welcome to Stock Price Prediction. How can I assist you today?"
            },
            'help': {
                'keywords': ['help', 'assist', 'guide', 'how to'],
                'response': "I can help you with:\n- Stock price predictions\n- Model explanations\n- Data interpretation\n- FAQs\n- Technical support"
            },
            'models': {
                'keywords': ['model', 'lstm', 'regression', 'forest', 'arima'],
                'response': "We use 4 prediction models:\n1. **LSTM** - Deep learning for time series\n2. **Linear Regression** - Simple trend analysis\n3. **Random Forest** - Ensemble learning approach\n4. **ARIMA** - Statistical forecasting\nEach model provides different perspectives on price movements."
            },
            'prediction': {
                'keywords': ['predict', 'forecast', 'prediction', 'future'],
                'response': "To make a prediction:\n1. Click 'Start Prediction'\n2. Select a stock symbol\n3. Choose prediction days (1-30)\n4. Click 'Predict'\nResults will show predicted prices and model comparisons."
            },
            'accuracy': {
                'keywords': ['accuracy', 'reliable', 'reliable', 'accurate'],
                'response': "Accuracy varies by stock and market conditions:\n- RMSE (Root Mean Square Error) measures prediction error\n- MAE (Mean Absolute Error) shows average deviation\n- Compare all models to find the best fit\n- Historical data improves predictions"
            },
            'data': {
                'keywords': ['data', 'download', 'export', 'csv'],
                'response': "You can:\n- Download historical stock data\n- Export as CSV for analysis\n- Choose custom date ranges\n- Use data in your own models"
            },
            'stock_symbols': {
                'keywords': ['symbol', 'stock', 'company', 'ticker'],
                'response': "Popular stocks available:\nAAPL (Apple), GOOGL (Google), MSFT (Microsoft), AMZN (Amazon), TSLA (Tesla), META (Meta), NFLX (Netflix), NVDA (NVIDIA), AMD (AMD), INTC (Intel)"
            },
            'theme': {
                'keywords': ['dark', 'light', 'theme', 'mode'],
                'response': "You can toggle between light and dark themes using the theme switch in the top right corner!"
            },
            'account': {
                'keywords': ['account', 'login', 'signup', 'register', 'password'],
                'response': "Account management features:\n- Secure login with email/username\n- Password reset available\n- Remember me option\n- Profile settings"
            },
            'faq': {
                'keywords': ['faq', 'frequently', 'question', 'common'],
                'response': "Check our FAQs page for:\n- Common questions about predictions\n- Model explanations\n- Data interpretation\n- Troubleshooting"
            },
            'default': {
                'keywords': [],
                'response': "I'm here to help with stock predictions! Ask me about models, predictions, data, or any other features."
            }
        }
    
    def get_response(self, user_input):
        """Get chatbot response based on user input"""
        user_input = user_input.lower().strip()
        
        # Find best matching response
        for key, data in self.responses.items():
            if key == 'default':
                continue
            
            for keyword in data['keywords']:
                if keyword in user_input:
                    return data['response']
        
        # Return default response if no match
        return self.responses['default']['response']
    
    def get_quick_tips(self):
        """Get quick tips for users"""
        tips = [
            "📊 Compare all 4 models to get the best prediction insights",
            "📈 RMSE and MAE metrics help you understand model accuracy",
            "📥 Download historical data to analyze trends yourself",
            "🔄 Check predictions regularly as markets change daily",
            "🌙 Use dark mode for comfortable viewing at night",
            "💾 Export charts as images or PDFs for reports"
        ]
        return tips
