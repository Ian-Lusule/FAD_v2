import os
import json
from pathlib import Path
from werkzeug.security import generate_password_hash

def create_file_structure():
    """Create the complete file structure for Fraud App Analyzer Flask"""
    
    # Define the directory structure
    structure = {
        "fraud-app-analyzer-flask": {
            "files": [
                "app.py",
                "config.py", 
                "requirements.txt",
                "file_store.py",
                "auth.py",
                "admin.py",
                "main.py",
                ".env",
                ".env.example",
                "README.md",
                "run.py"
            ],
            "directories": {
                "modules": [
                    "__init__.py",
                    "data_fetcher.py",
                    "sentiment_analyzer.py", 
                    "report_generator.py",
                    "email_sender.py"
                ],
                "templates": {
                    "auth": [
                        "login.html",
                        "register.html",
                        "change_password.html",
                        "contact_admin.html",
                        "dashboard.html"
                    ],
                    "admin": [
                        "dashboard.html",
                        "users.html",
                        "messages.html",
                        "analytics.html"
                    ],
                    "analysis": [
                        "results.html",
                        "compare.html"
                    ],
                    "":[
                    "base.html",
                    "index.html",
                    "error.html"]
                },
                "static": {
                    "css": ["style.css"],
                    "js": ["main.js"]
                },
                "data": {
                    "results": []  # Empty directory for results
                }
            }
        }
    }

    # Create the structure
    base_dir = "fraud-app-analyzer-flask"
    
    # Create base directory
    os.makedirs(base_dir, exist_ok=True)
    print(f"Created directory: {base_dir}")
    
    # Create files in root
    for filename in structure["fraud-app-analyzer-flask"]["files"]:
        filepath = os.path.join(base_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            # Add minimal content to .env.example
            if filename == ".env.example":
                f.write("""# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
FLASK_DEBUG=1

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Application Settings
MAX_REVIEWS_DEFAULT=200
DEFAULT_FRAUD_THRESHOLD=30.0
DEFAULT_COUNTRY=us
""")
            elif filename == "requirements.txt":
                f.write("""Flask==2.3.3
Flask-Login==0.6.3
Flask-Mail==0.9.1
google-play-scraper==1.2.5
textblob==0.17.1
pandas==2.1.4
matplotlib==3.8.0
wordcloud==1.9.3
reportlab==4.0.8
numpy==1.24.4
scikit-learn==1.3.2
python-dotenv==1.0.0
Werkzeug==2.3.7
""")
            elif filename == "README.md":
                f.write("""# Fraud App Analyzer - Flask Edition

A Flask web application for analyzing Google Play Store apps for potential fraud risks.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and configure settings
3. Run: `python app.py`
4. Visit: http://localhost:5000

## Default Accounts
- Admin: admin / admin123
- User: user / user123

## Features
- App analysis with sentiment detection
- User authentication and dashboard
- Admin panel for management
- Export reports as CSV/PDF
- App comparison tool
""")
            elif filename == "run.py":
                f.write("""#!/usr/bin/env python3
\"\"\"
Run script for Fraud App Analyzer Flask Application
\"\"\"

import os
import sys
from app import app

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/results', exist_ok=True)
    
    # Run the application
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', '1') == '1'
    )
""")
            else:
                f.write(f"# {filename}\n# File created for Fraud App Analyzer Flask\n")
        print(f"Created file: {filepath}")
    
    # Create directories and their files
    def create_dirs(parent, dirs):
        for dir_name, contents in dirs.items():
            dir_path = os.path.join(parent, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            
            if isinstance(contents, list):
                # Directory with files
                for filename in contents:
                    filepath = os.path.join(dir_path, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        if filename == "__init__.py":
                            f.write("""\"\"\"
Modules package for Fraud App Analyzer Flask
\"\"\"
""")
                        elif filename.endswith('.py'):
                            f.write(f"# {filename}\n# Module for Fraud App Analyzer Flask\n")
                        elif filename.endswith('.html'):
                            f.write(f"<!-- {filename} -->\n<!-- Template for Fraud App Analyzer Flask -->\n")
                        elif filename.endswith('.css'):
                            f.write(f"/* {filename} */\n/* Styles for Fraud App Analyzer Flask */\n")
                        elif filename.endswith('.js'):
                            f.write(f"// {filename}\n// JavaScript for Fraud App Analyzer Flask\n")
                    print(f"Created file: {filepath}")
            elif isinstance(contents, dict):
                # Nested directory structure
                create_dirs(dir_path, contents)
            else:
                # Single file in directory
                filepath = os.path.join(dir_path, contents)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {contents}\n")
                print(f"Created file: {filepath}")
    
    create_dirs(base_dir, structure["fraud-app-analyzer-flask"]["directories"])
    
    # Create minimal config.py
    config_content = """import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    \"\"\"Flask application configuration\"\"\"
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')
    RESULTS_FOLDER = os.path.join(DATA_FOLDER, 'results')
    
    # Authentication
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # App settings
    MAX_REVIEWS_DEFAULT = 200
    DEFAULT_COUNTRY = 'us'
    DEFAULT_FRAUD_THRESHOLD = 30.0
    POSITIVE_THRESHOLD = 0.1
    NEGATIVE_THRESHOLD = -0.1

# Ensure directories exist
os.makedirs(Config.DATA_FOLDER, exist_ok=True)
os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
"""
    
    config_path = os.path.join(base_dir, "config.py")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    # Create minimal app.py
    app_content = """from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# Initialize Flask extensions
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    \"\"\"Application factory function\"\"\"
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints will be added here
    # from auth import auth_bp
    # from admin import admin_bp
    # from main import main_bp
    # app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(admin_bp, url_prefix='/admin')
    # app.register_blueprint(main_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
"""
    
    app_path = os.path.join(base_dir, "app.py")
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
    
    # Create users.json with admin account
    data_dir = os.path.join(base_dir, "data")
    users_file = os.path.join(data_dir, "users.json")
    
    # Create admin user with hashed password
    admin_user = {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": generate_password_hash("admin123"),
        "is_admin": True,
        "created_at": "2024-01-01T00:00:00",
        "last_login": None
    }
    
    # Create regular user
    regular_user = {
        "id": 2,
        "username": "user",
        "email": "user@example.com",
        "password_hash": generate_password_hash("user123"),
        "is_admin": False,
        "created_at": "2024-01-01T00:00:00",
        "last_login": None
    }
    
    users_data = [admin_user, regular_user]
    
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2)
    print(f"Created admin account in: {users_file}")
    
    # Create other data files
    search_logs_file = os.path.join(data_dir, "search_logs.csv")
    with open(search_logs_file, 'w', encoding='utf-8') as f:
        f.write("timestamp,user_id,app_id,country,app_name\n")
    print(f"Created file: {search_logs_file}")
    
    messages_file = os.path.join(data_dir, "messages.json")
    with open(messages_file, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    print(f"Created file: {messages_file}")
    
    # Create .env file from .env.example
    env_example = os.path.join(base_dir, ".env.example")
    env_file = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_example):
        with open(env_example, 'r', encoding='utf-8') as src:
            with open(env_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"Created .env file from .env.example: {env_file}")
    
    print("\n" + "="*50)
    print("File structure created successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. cd fraud-app-analyzer-flask")
    print("2. pip install -r requirements.txt")
    print("3. python app.py")
    print("\nDefault accounts:")
    print("  Admin: username='admin', password='admin123'")
    print("  User:  username='user',  password='user123'")
    print("\nThe application will be available at: http://localhost:5000")

if __name__ == "__main__":
    create_file_structure()