import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Flask application configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    RESULTS_FOLDER = os.path.join(DATA_FOLDER, 'results')
    
    # Authentication
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Email configuration
    # Email configuration (can be overridden via environment variables)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'mail.shule.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    # Default SMTP credentials provided (override with env vars if needed)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'info@shule.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'Strong_PassWD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # App settings
    MAX_REVIEWS_DEFAULT = 200
    DEFAULT_COUNTRY = 'ke'
    DEFAULT_FRAUD_THRESHOLD = 30.0
    POSITIVE_THRESHOLD = 0.1
    NEGATIVE_THRESHOLD = -0.1
    
    # Risk messaging
    RISK_WARNING_SHORT = "Strong indicators of potential risk identified"
    RISK_ADVICE_UI = "Exercise caution and conduct further independent research before downloading, using, or trusting this app. Consider reporting the app directly to the Google Play Store or relevant authorities if you have concerns. Look for red flags such as unclear developer history, excessive permissions, or consistent scam reports elsewhere."

# Ensure directories exist
os.makedirs(Config.DATA_FOLDER, exist_ok=True)
os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)