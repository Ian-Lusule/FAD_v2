"""
Modules package for Fraud App Analyzer.
"""

from modules.data_fetcher import fetch_app_details, fetch_reviews, fetch_multiple_apps
from modules.sentiment_analyzer import (
    analyze_sentiment, 
    calculate_sentiment_metrics, 
    get_score_color,
    detect_risk_keywords,
    NEGATIVE_KEYWORDS
)
from modules.report_generator import (
    create_sentiment_trend_chart,
    create_word_cloud_image,
    generate_single_app_pdf_report,
    generate_comparison_pdf,
    RISK_WARNING_SHORT,
    RISK_ADVICE_UI,
    DISCLAIMER_TEXT,
    DISCLAIMER_LINK
)
from modules.email_sender import (
    send_analysis_email,
    send_welcome_email,
    RISK_WARNING_EMAIL,
    RISK_ADVICE_EMAIL
)

__all__ = [
    # Data fetcher
    'fetch_app_details',
    'fetch_reviews',
    'fetch_multiple_apps',
    
    # Sentiment analyzer
    'analyze_sentiment',
    'calculate_sentiment_metrics',
    'get_score_color',
    'detect_risk_keywords',
    'NEGATIVE_KEYWORDS',
    
    # Report generator
    'create_sentiment_trend_chart',
    'create_word_cloud_image',
    'generate_single_app_pdf_report',
    'generate_comparison_pdf',
    'RISK_WARNING_SHORT',
    'RISK_ADVICE_UI',
    'DISCLAIMER_TEXT',
    'DISCLAIMER_LINK',
    
    # Email sender
    'send_analysis_email',
    'send_welcome_email',
    'RISK_WARNING_EMAIL',
    'RISK_ADVICE_EMAIL'
]