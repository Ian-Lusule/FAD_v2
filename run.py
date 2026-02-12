#!/usr/bin/env python3
"""
Run script for Fraud App Analyzer Flask Application
"""

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
