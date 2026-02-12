from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from flask_login import login_required, current_user
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import traceback
import re
from config import Config
from file_store import append_search_log, save_result
import json

main_bp = Blueprint('main', __name__)

# Import modules (preserving original functionality)
try:
    from modules.data_fetcher import fetch_app_details, fetch_reviews, search_apps
    from modules.sentiment_analyzer import analyze_sentiment, calculate_sentiment_metrics, NEGATIVE_KEYWORDS
    from modules.report_generator import (
        create_sentiment_trend_chart, create_word_cloud_image,
        generate_single_app_pdf_report, RISK_WARNING_SHORT, RISK_ADVICE_UI
    )
    from modules.email_sender import send_analysis_email
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    MODULES_AVAILABLE = False

# Country options (same as original)
COUNTRIES = ["us", "gb", "in", "ke", "tz", "ca", "de", "fr", "jp", "ng", "au"]

# Matplotlib configuration to avoid threading issues
import matplotlib
matplotlib.use('Agg')

def extract_app_id(app_input):
    """Extract app ID from Play Store URL or return input as-is"""
    # If it looks like a URL, extract the ID
    if 'play.google.com' in app_input:
        match = re.search(r'id=([a-zA-Z0-9._]+)', app_input)
        if match:
            return match.group(1)
    
    # If it contains dots, assume it's an app ID
    if '.' in app_input and ' ' not in app_input:
        return app_input
    
    # Otherwise, try to extract from URL patterns
    patterns = [
        r'/([a-zA-Z0-9._]+)/?$',
        r'=([a-zA-Z0-9._]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, app_input)
        if match:
            return match.group(1)
    
    return app_input

@main_bp.route('/')
def index():
    """Homepage with search form"""
    # Get form values from session if they exist
    default_country = session.get('last_country', Config.DEFAULT_COUNTRY)
    default_threshold = session.get('last_fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD)
    default_max_reviews = session.get('last_max_reviews', Config.MAX_REVIEWS_DEFAULT)
    
    # Get search results if any
    search_results = session.get('search_results', [])
    show_search_results = session.get('show_search_results', False)
    
    return render_template('index.html', 
                         countries=COUNTRIES,
                         default_country=default_country,
                         default_threshold=default_threshold,
                         default_max_reviews=default_max_reviews,
                         search_results=search_results,
                         show_search_results=show_search_results)

@main_bp.route('/search', methods=['POST'])
def search_apps_route():
    """Search for apps by name"""
    try:
        query = request.form.get('app_input', '').strip()
        country = request.form.get('country', Config.DEFAULT_COUNTRY)
        
        if not query:
            flash('Please enter an app name to search', 'warning')
            return redirect(url_for('main.index'))
        
        # Check if it's a URL with app ID
        app_id = extract_app_id(query)
        
        # If it looks like an app ID (contains dot), try to fetch directly
        if '.' in query and ' ' not in query and app_id == query:
            # It's likely an app ID, fetch directly
            app_details = fetch_app_details(app_id, country)
            if app_details:
                # Store in session and redirect to analyze
                session['selected_app_id'] = app_id
                session['selected_app_details'] = {
                    'title': app_details.get('title'),
                    'icon': app_details.get('icon'),
                    'score': app_details.get('score'),
                    'installs': app_details.get('installs'),
                    'developer': app_details.get('developer')
                }
                session['show_search_results'] = False
                return redirect(url_for('main.analyze_direct', app_id=app_id))
            else:
                flash(f'App with ID "{app_id}" not found. Trying search instead...', 'info')
        
        # Perform search
        search_results = search_apps(query, country, limit=10)
        
        if not search_results:
            flash(f'No apps found for "{query}" in {country.upper()}', 'warning')
            session['search_results'] = []
            session['show_search_results'] = False
        else:
            session['search_results'] = search_results
            session['show_search_results'] = True
            flash(f'Found {len(search_results)} apps for "{query}"', 'success')
        
        # Store form values
        session['last_country'] = country
        session['last_query'] = query
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Error searching apps: {e}")
        traceback.print_exc()
        flash(f'Error searching for apps: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/analyze/<app_id>')
def analyze_direct(app_id):
    """Analyze a specific app directly"""
    try:
        country = session.get('last_country', Config.DEFAULT_COUNTRY)
        fraud_threshold = session.get('last_fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD)
        max_reviews = session.get('last_max_reviews', Config.MAX_REVIEWS_DEFAULT)
        
        # Fetch app details
        app_details = fetch_app_details(app_id, country)
        if not app_details:
            flash(f'Could not fetch app details for "{app_id}". The app may not exist in the selected country.', 'danger')
            return redirect(url_for('main.index'))
        
        # Fetch reviews
        reviews = fetch_reviews(app_id, country, max_reviews)
        if not reviews:
            flash(f'No reviews found for "{app_details.get("title", app_id)}"', 'warning')
        
        # Convert to DataFrame
        df = pd.DataFrame(reviews) if reviews else pd.DataFrame(columns=['content', 'score', 'thumbsUpCount', 'at'])
        
        # Perform sentiment analysis
        if 'content' in df.columns and not df.empty:
            df['polarity'] = df['content'].apply(analyze_sentiment)
            df['sentiment'] = df['polarity'].apply(
                lambda p: 'Positive' if p > Config.POSITIVE_THRESHOLD 
                else ('Negative' if p < Config.NEGATIVE_THRESHOLD 
                else 'Neutral')
            )
        else:
            df['polarity'] = 0
            df['sentiment'] = 'Neutral'
        
        # Calculate metrics
        sentiment_counts, positive_pct, negative_pct, neutral_pct, app_rating_score, playstore_score = calculate_sentiment_metrics(df, app_details)
        
        # Create trend data
        trend_df = create_trend_data(df) if 'at' in df.columns and not df.empty else pd.DataFrame()
        
        # Create visualizations
        sentiment_chart = create_sentiment_chart_image(sentiment_counts)
        trend_chart = create_trend_chart_image(trend_df) if not trend_df.empty else None
        
        # Create word cloud
        all_text = " ".join(df['content'].dropna().astype(str)) if 'content' in df.columns else ""
        wordcloud = create_wordcloud_image(all_text) if all_text.strip() else None
        
        # Prepare result data
        result_data = {
            'app_id': app_id,
            'app_name': app_details.get('title', 'Unknown App'),
            'app_details': {
                'title': app_details.get('title'),
                'developer': app_details.get('developer'),
                'score': app_details.get('score'),
                'installs': app_details.get('installs'),
                'price': app_details.get('price'),
                'free': app_details.get('free'),
                'url': app_details.get('url')
            },
            'analysis_date': datetime.now().isoformat(),
            'country': country,
            'max_reviews': max_reviews,
            'fraud_threshold': fraud_threshold,
            'metrics': {
                'total_reviews': len(df),
                'positive_pct': positive_pct,
                'negative_pct': negative_pct,
                'neutral_pct': neutral_pct,
                'app_rating_score': app_rating_score,
                'playstore_score': playstore_score
            },
            'sentiment_counts': sentiment_counts.to_dict() if not sentiment_counts.empty else {},
            'risk_detected': negative_pct > fraud_threshold,
            'risk_message': RISK_WARNING_SHORT if negative_pct > fraud_threshold else "No significant risk indicators found"
        }
        
        # Log search and save result if user is logged in
        user_id = current_user.id if current_user.is_authenticated else None
        append_search_log(user_id, app_id, country, app_details.get('title', ''))
        
        if current_user.is_authenticated:
            save_result(current_user.id, result_data)
        
        # Store minimal data in session for export/email
        session['last_analysis'] = {
            'app_id': app_id,
            'app_name': app_details.get('title', 'Unknown App'),
            'country': country,
            'fraud_threshold': fraud_threshold,
            'positive_pct': positive_pct,
            'negative_pct': negative_pct,
            'neutral_pct': neutral_pct,
            'app_rating_score': app_rating_score,
            'playstore_score': playstore_score,
            'risk_detected': negative_pct > fraud_threshold
        }
        
        # Clear search results
        session['search_results'] = []
        session['show_search_results'] = False
        
        return render_template('analysis/results.html',
                             app_details=app_details,
                             df=df,
                             sentiment_counts=sentiment_counts,
                             positive_pct=positive_pct,
                             negative_pct=negative_pct,
                             neutral_pct=neutral_pct,
                             app_rating_score=app_rating_score,
                             playstore_score=playstore_score,
                             fraud_threshold=fraud_threshold,
                             risk_detected=negative_pct > fraud_threshold,
                             risk_message=RISK_WARNING_SHORT if negative_pct > fraud_threshold else "No significant risk indicators found",
                             sentiment_chart=sentiment_chart,
                             trend_chart=trend_chart,
                             wordcloud=wordcloud,
                             countries=COUNTRIES,
                             selected_country=country,
                             selected_threshold=fraud_threshold,
                             selected_max_reviews=max_reviews)
    
    except Exception as e:
        print(f"Error in direct analysis: {e}")
        traceback.print_exc()
        flash(f'An error occurred during analysis: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/compare/add/<app_id>')
def add_to_compare(app_id):
    """Add an app to comparison"""
    try:
        country = session.get('last_country', Config.DEFAULT_COUNTRY)
        
        # Fetch app details
        app_details = fetch_app_details(app_id, country)
        if not app_details:
            flash(f'Could not fetch app details for "{app_id}"', 'danger')
            return redirect(url_for('main.index'))
        
        # Initialize comparison list if not exists
        if 'compare_apps' not in session:
            session['compare_apps'] = []
        
        # Check if app already in comparison
        app_exists = any(app['app_id'] == app_id for app in session['compare_apps'])
        
        if not app_exists:
            # Add app to comparison (max 2 apps)
            if len(session['compare_apps']) < 2:
                session['compare_apps'].append({
                    'app_id': app_id,
                    'title': app_details.get('title', 'Unknown App'),
                    'icon': app_details.get('icon'),
                    'score': app_details.get('score'),
                    'developer': app_details.get('developer')
                })
                flash(f'Added "{app_details.get("title")}" to comparison', 'success')
            else:
                flash('Maximum 2 apps can be compared. Remove one first.', 'warning')
        else:
            flash(f'"{app_details.get("title")}" is already in comparison', 'info')
        
        # Clear search results
        session['search_results'] = []
        session['show_search_results'] = False
        
        # Redirect to comparison page if we have 2 apps
        if len(session.get('compare_apps', [])) == 2:
            return redirect(url_for('main.compare'))
        else:
            return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Error adding to compare: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/compare/remove/<int:index>')
def remove_from_compare(index):
    """Remove an app from comparison"""
    try:
        if 'compare_apps' in session and 0 <= index < len(session['compare_apps']):
            removed_app = session['compare_apps'].pop(index)
            flash(f'Removed "{removed_app.get("title")}" from comparison', 'info')
        
        return redirect(url_for('main.compare'))
        
    except Exception as e:
        print(f"Error removing from compare: {e}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/compare')
def compare():
    """Compare apps side by side"""
    compare_apps = session.get('compare_apps', [])
    
    if len(compare_apps) < 2:
        flash('Please add 2 apps to compare', 'warning')
        return redirect(url_for('main.index'))
    
    try:
        country = session.get('last_country', Config.DEFAULT_COUNTRY)
        max_reviews = session.get('last_max_reviews', Config.MAX_REVIEWS_DEFAULT) // 2
        
        app1_data = compare_apps[0]
        app2_data = compare_apps[1]
        
        # Get metrics for comparison
        app1_metrics = get_sentiment_metrics_for_comparison(app1_data['app_id'], country, max_reviews)
        app2_metrics = get_sentiment_metrics_for_comparison(app2_data['app_id'], country, max_reviews)
        
        # Fetch full details for display
        app1_details = fetch_app_details(app1_data['app_id'], country)
        app2_details = fetch_app_details(app2_data['app_id'], country)
        
        return render_template('analysis/compare.html',
                             app1_details=app1_details or app1_data,
                             app2_details=app2_details or app2_data,
                             app1_metrics=app1_metrics,
                             app2_metrics=app2_metrics,
                             countries=COUNTRIES)
    
    except Exception as e:
        print(f"Error in comparison: {e}")
        traceback.print_exc()
        flash(f'An error occurred during comparison: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/clear_search')
def clear_search():
    """Clear search results"""
    session['search_results'] = []
    session['show_search_results'] = False
    return redirect(url_for('main.index'))

# ... rest of the existing functions (create_trend_data, create_sentiment_chart_image, etc.) ...

@main_bp.route('/send_email_report', methods=['POST'])
@login_required
def send_email_report():
    """Send analysis report via email - minimal implementation"""
    recipient_email = request.form.get('recipient_email', '').strip()
    recipient_name = request.form.get('recipient_name', '').strip()
    
    if not recipient_email or not recipient_name:
        flash('Please enter both name and email', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    try:
        # Simple email logic - you'll need to configure email settings
        flash(f'Email report would be sent to {recipient_email}. Configure email settings in .env file.', 'info')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('main.index'))

# ... rest of the helper functions ...