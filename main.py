from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from flask_login import login_required, current_user
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import traceback
import re
import json
import uuid
import os
from config import Config
from file_store import append_search_log, save_result
from file_store import load_messages, save_messages, add_message, get_user_by_id, get_user_messages, delete_message, mark_message_as_read, mark_message_as_unread
from types import SimpleNamespace

# Set Matplotlib to non-interactive backend to avoid threading issues in Flask
matplotlib.use('Agg')

main_bp = Blueprint('main', __name__)

# Import modules
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

# Country options
COUNTRIES = ["us", "gb", "in", "ke", "tz", "ca", "de", "fr", "jp", "ng", "au"]

# --- HELPER FUNCTIONS ---

def extract_app_id(app_input):
    """Extract app ID from Play Store URL or return input as-is"""
    if 'play.google.com' in app_input:
        match = re.search(r'id=([a-zA-Z0-9._]+)', app_input)
        if match:
            return match.group(1)
    
    if '.' in app_input and ' ' not in app_input:
        return app_input
    
    patterns = [r'/([a-zA-Z0-9._]+)/?$', r'=([a-zA-Z0-9._]+)']
    for pattern in patterns:
        match = re.search(pattern, app_input)
        if match:
            return match.group(1)
    
    return app_input

def create_trend_data(df):
    """Create sentiment trend data with date conversion to strings"""
    if 'at' not in df.columns or df.empty:
        return pd.DataFrame()
    try:
        df['date'] = pd.to_datetime(df['at']).dt.date
        trend_df = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
        trend_df.index = trend_df.index.astype(str)
        return trend_df
    except Exception as e:
        print(f"Error creating trend data: {e}")
        return pd.DataFrame()

def create_sentiment_chart_image(sentiment_counts):
    if sentiment_counts is None or sentiment_counts.empty: return None
    try:
        plt.switch_backend('Agg')
        fig, ax = plt.subplots(figsize=(6, 4))
        sentiment_counts.plot(kind='bar', ax=ax, color=['#28a745', '#dc3545', '#ffc107'])
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except: return None

def create_trend_chart_image(trend_df):
    if trend_df is None or trend_df.empty: return None
    try:
        plt.switch_backend('Agg')
        fig = create_sentiment_trend_chart(trend_df, for_pdf=False)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except: return None

def create_wordcloud_image(all_text):
    if not all_text or not all_text.strip(): return None
    try:
        plt.switch_backend('Agg')
        fig = create_word_cloud_image(all_text, for_pdf=False)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
    except: return None

def get_sentiment_metrics_for_comparison(app_id, country, max_reviews):
    try:
        reviews = fetch_reviews(app_id, country, max_reviews)
        if not reviews:
            return {"total": 0, "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0, "app_rating_score": 0.0}
        df = pd.DataFrame(reviews)
        df['polarity'] = df['content'].apply(analyze_sentiment)
        df['sentiment'] = df['polarity'].apply(lambda p: 'Positive' if p > 0.1 else ('Negative' if p < -0.1 else 'Neutral'))
        try:
            _, pos, neg, neu, rating, _ = calculate_sentiment_metrics(df, None)
        except Exception:
            pos = neg = neu = rating = 0.0
        return {"total": len(df), "positive_pct": pos, "negative_pct": neg, "neutral_pct": neu, "app_rating_score": rating}
    except Exception:
        return {"total": 0, "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0, "app_rating_score": 0.0}

# --- ROUTES ---

@main_bp.route('/')
def index():
    """Homepage with search form and retained values"""
    default_country = session.get('last_country', Config.DEFAULT_COUNTRY)
    default_threshold = session.get('last_fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD)
    default_max_reviews = session.get('last_max_reviews', Config.MAX_REVIEWS_DEFAULT)
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
        # Optional user-configurable analysis settings
        try:
            max_reviews = int(request.form.get('max_reviews', Config.MAX_REVIEWS_DEFAULT))
        except Exception:
            max_reviews = Config.MAX_REVIEWS_DEFAULT
        try:
            fraud_threshold = float(request.form.get('fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD))
        except Exception:
            fraud_threshold = Config.DEFAULT_FRAUD_THRESHOLD
        
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
                # Store minimal data in session
                session['selected_app_id'] = app_id
                session['selected_app_name'] = app_details.get('title', app_id)
                session['show_search_results'] = False
                # Clear large search results
                if 'search_results' in session:
                    del session['search_results']
                return redirect(url_for('main.analyze_direct', app_id=app_id))
            else:
                flash(f'App with ID "{app_id}" not found. Trying search instead...', 'info')
        
        # Perform search (fetch more to allow client-side paging/sorting)
        search_results = search_apps(query, country, limit=50)
        
        if not search_results:
            flash(f'No apps found for "{query}" in {country.upper()}', 'warning')
            session['show_search_results'] = False
            # Clear search results from session
            if 'search_results' in session:
                del session['search_results']
        else:
            # Store only minimal data in session
            # Store up to 20 results for display by default
            session['search_results'] = [
                {
                    'appId': app.get('appId'),
                    'title': app.get('title'),
                    'developer': app.get('developer'),
                    'score': app.get('score'),
                    'installs': app.get('installs'),
                    'icon': app.get('icon')  # include icon for display
                }
                for app in search_results[:20]
            ]
            session['search_per_page'] = 20
            session['show_search_results'] = True
            flash(f'Found {len(search_results)} apps for "{query}"', 'success')
        
        # Store form values (minimal)
        session['last_country'] = country
        session['last_max_reviews'] = max(10, min(max_reviews, 1000))
        session['last_fraud_threshold'] = max(1.0, min(fraud_threshold, 100.0))
        session['last_query'] = query
        
        # Clear other large session data (keep compare_apps so comparisons persist across searches)
        for key in ['last_analysis', 'last_analysis_file', 'last_analysis_summary']:
            if key in session:
                del session[key]
        
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Error searching apps: {e}")
        traceback.print_exc()
        flash(f'Error searching for apps: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/analyze/<app_id>')
def analyze_direct(app_id):
    """Analyze a specific app ID directly"""
    if not MODULES_AVAILABLE:
        flash('Analysis modules not available.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        country = session.get('last_country', Config.DEFAULT_COUNTRY)
        fraud_threshold = session.get('last_fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD)
        max_reviews = session.get('last_max_reviews', Config.MAX_REVIEWS_DEFAULT)
        
        app_details = fetch_app_details(app_id, country)
        if not app_details:
            flash(f'Could not fetch details for "{app_id}".', 'danger')
            return redirect(url_for('main.index'))
        
        # Allow sorting of reviews via query param: sort=newest|oldest|helpful
        sort_mode = request.args.get('sort', 'newest')
        reviews = fetch_reviews(app_id, country, max_reviews)
        df = pd.DataFrame(reviews) if reviews else pd.DataFrame(columns=['content', 'score', 'thumbsUpCount', 'at'])
        
        if 'content' in df.columns and not df.empty:
            df['polarity'] = df['content'].apply(analyze_sentiment)
            df['sentiment'] = df['polarity'].apply(
                lambda p: 'Positive' if p > Config.POSITIVE_THRESHOLD 
                else ('Negative' if p < Config.NEGATIVE_THRESHOLD else 'Neutral')
            )

        # Sorting
        try:
            if sort_mode == 'oldest':
                df = df.sort_values(by='at', ascending=True)
            elif sort_mode == 'helpful' and 'thumbsUpCount' in df.columns:
                df = df.sort_values(by='thumbsUpCount', ascending=False)
            else:
                # default newest
                df = df.sort_values(by='at', ascending=False)
        except Exception:
            pass
        
        metrics = calculate_sentiment_metrics(df, app_details)
        sentiment_counts, pos_pct, neg_pct, neu_pct, rating_score, ps_score = metrics
        # Classification metrics (accuracy/precision/recall/f1) based on negative-keyword weak labels
        try:
            from modules.sentiment_analyzer import compute_classification_metrics
            classification_metrics = compute_classification_metrics(df)
        except Exception:
            classification_metrics = {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

        # Normalize classification_metrics to always include confusion and examples
        if not isinstance(classification_metrics, dict):
            try:
                classification_metrics = dict(classification_metrics)
            except Exception:
                classification_metrics = {}

        classification_metrics.setdefault('confusion', {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0})
        classification_metrics.setdefault('examples', {'tp': [], 'tn': [], 'fp': [], 'fn': []})

        # Convert nested dicts to SimpleNamespace so templates can use dot access
        def to_namespace(obj):
            if isinstance(obj, dict):
                return SimpleNamespace(**{k: to_namespace(v) for k, v in obj.items()})
            if isinstance(obj, list):
                return [to_namespace(v) for v in obj]
            return obj

        classification_metrics = to_namespace(classification_metrics)
        
        trend_df = create_trend_data(df)
        sentiment_chart = create_sentiment_chart_image(sentiment_counts)
        trend_chart = create_trend_chart_image(trend_df)
        all_text = " ".join(df['content'].dropna().astype(str)) if 'content' in df.columns else ""
        wordcloud = create_wordcloud_image(all_text)
        
        # Ensure classification metrics are JSON-serializable (dicts/lists), not SimpleNamespace
        def ns_to_plain(o):
            if isinstance(o, dict):
                return {k: ns_to_plain(v) for k, v in o.items()}
            if isinstance(o, list):
                return [ns_to_plain(v) for v in o]
            # SimpleNamespace or other objects with __dict__
            if hasattr(o, '__dict__'):
                try:
                    return ns_to_plain(vars(o))
                except Exception:
                    return str(o)
            return o

        serializable_classification_metrics = ns_to_plain(classification_metrics)

        # Save analysis to a server-side JSON file and store a small pointer in session
        analysis_payload = {
            'app_id': app_id,
            'app_details': app_details,
            'df_dict': df.to_dict() if not df.empty else {},
            'trend_dict': trend_df.to_dict() if not trend_df.empty else {},
            'sentiment_counts': sentiment_counts.to_dict() if not sentiment_counts.empty else {},
            'metrics_summary': {'positive_pct': pos_pct, 'negative_pct': neg_pct, 'app_rating_score': rating_score},
            'classification_metrics': serializable_classification_metrics,
            'fraud_threshold': fraud_threshold,
            'all_text': all_text,
            'saved_at': datetime.now().isoformat()
        }

        # Ensure results folder exists
        os.makedirs(Config.RESULTS_FOLDER, exist_ok=True)
        analysis_id = f"last_{uuid.uuid4().hex}.json"
        analysis_path = os.path.join(Config.RESULTS_FOLDER, analysis_id)
        try:
            with open(analysis_path, 'w') as af:
                json.dump(analysis_payload, af, default=str)
            # Store pointer and small summary in session
            session['last_analysis_file'] = analysis_id
            session['last_analysis_summary'] = {
                'app_id': app_id,
                'app_title': app_details.get('title'),
                'metrics_summary': {'positive_pct': pos_pct, 'negative_pct': neg_pct, 'app_rating_score': rating_score},
                'fraud_threshold': fraud_threshold
            }
        except Exception as e:
            print(f"Failed to save analysis payload: {e}")
        
        return render_template('analysis/results.html',
                             app_details=app_details, df=df, sentiment_counts=sentiment_counts,
                             positive_pct=pos_pct, negative_pct=neg_pct, neutral_pct=neu_pct,
                             app_rating_score=rating_score, playstore_score=ps_score,
                             fraud_threshold=fraud_threshold, risk_detected=neg_pct > fraud_threshold,
                             risk_message=RISK_WARNING_SHORT if neg_pct > fraud_threshold else "No risk indicators",
                             sentiment_chart=sentiment_chart, trend_chart=trend_chart, wordcloud=wordcloud, countries=COUNTRIES,
                             classification_metrics=classification_metrics)
    except Exception as e:
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'danger')
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
            # Add minimal app data to comparison (max 2 apps)
            if len(session['compare_apps']) < 2:
                session['compare_apps'].append({
                    'app_id': app_id,
                    'title': app_details.get('title', 'Unknown App'),
                    'developer': app_details.get('developer', 'Unknown'),
                    'score': app_details.get('score', 0)
                })
                flash(f'Added "{app_details.get("title")}" to comparison', 'success')
            else:
                flash('Maximum 2 apps can be compared. Remove one first.', 'warning')
        else:
            flash(f'"{app_details.get("title")}" is already in comparison', 'info')
        
        # Clear search results to reduce session size
        if 'search_results' in session:
            del session['search_results']
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
        
@main_bp.route('/compare')
def compare():
    apps = session.get('compare_apps', [])
    if len(apps) < 2:
        flash('Add 2 apps to compare.', 'warning')
        return redirect(url_for('main.index'))
    
    country = session.get('last_country', Config.DEFAULT_COUNTRY)
    m1 = get_sentiment_metrics_for_comparison(apps[0]['app_id'], country, 100)
    m2 = get_sentiment_metrics_for_comparison(apps[1]['app_id'], country, 100)
    d1 = fetch_app_details(apps[0]['app_id'], country)
    d2 = fetch_app_details(apps[1]['app_id'], country)
    
    return render_template('analysis/compare.html', app1_details=d1, app2_details=d2, 
                           app1_metrics=m1, app2_metrics=m2, countries=COUNTRIES)

@main_bp.route('/compare/remove/<int:index>')
def remove_from_compare(index):
    if 'compare_apps' in session and 0 <= index < len(session['compare_apps']):
        session['compare_apps'].pop(index)
    return redirect(url_for('main.compare') if session.get('compare_apps') else url_for('main.index'))

@main_bp.route('/export/csv')
@login_required
def export_csv():
    if 'last_analysis_file' not in session: return redirect(url_for('main.index'))
    analysis_path = os.path.join(Config.RESULTS_FOLDER, session['last_analysis_file'])
    try:
        with open(analysis_path, 'r') as f:
            data = json.load(f)
    except Exception:
        return redirect(url_for('main.index'))
    df = pd.DataFrame.from_dict(data.get('df_dict', {}))
    csv_data = df[['at', 'content', 'sentiment', 'polarity']].to_csv(index=False)
    return send_file(io.BytesIO(csv_data.encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f"{data['app_id']}_analysis.csv")

@main_bp.route('/export/pdf')
@login_required
def export_pdf():
    if 'last_analysis_file' not in session: return redirect(url_for('main.index'))
    analysis_path = os.path.join(Config.RESULTS_FOLDER, session['last_analysis_file'])
    try:
        with open(analysis_path, 'r') as f:
            data = json.load(f)
    except Exception:
        return redirect(url_for('main.index'))
    df = pd.DataFrame.from_dict(data.get('df_dict', {}))
    trend_df = pd.DataFrame.from_dict(data.get('trend_dict', {}))
    # load classification metrics if available
    classification_metrics = data.get('classification_metrics', None)
    pdf_buffer = generate_single_app_pdf_report(
        data['app_id'], data['app_details'], df, pd.Series(data.get('sentiment_counts', {})),
        data.get('metrics_summary', {}).get('positive_pct', 0.0),
        data.get('metrics_summary', {}).get('negative_pct', 0.0),
        data.get('metrics_summary', {}).get('neutral_pct', 0.0) if data.get('metrics_summary') else 0.0,
        data.get('metrics_summary', {}).get('app_rating_score', 0.0),
        data.get('playstore_score', 0.0) if data.get('playstore_score') else 0.0,
        data.get('fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD),
        trend_df, data.get('all_text', ''), pd.DataFrame(), classification_metrics
    )
    return send_file(io.BytesIO(pdf_buffer.getvalue()), mimetype='application/pdf', as_attachment=True, download_name=f"{data['app_id']}_report.pdf")


@main_bp.route('/save_analysis', methods=['POST'])
@login_required
def save_analysis():
    """Save the last analysis for the logged-in user"""
    if 'last_analysis_file' not in session:
        flash('No analysis to save', 'danger')
        return redirect(url_for('main.index'))
    analysis_path = os.path.join(Config.RESULTS_FOLDER, session['last_analysis_file'])
    try:
        with open(analysis_path, 'r') as f:
            data = json.load(f)
    except Exception:
        flash('Failed to load analysis data', 'danger')
        return redirect(url_for('main.index'))

    # Use file_store.save_result to persist under user folder
    from file_store import save_result as fs_save_result
    result_data = {
        'app_id': data.get('app_id'),
        'app_name': data.get('app_details', {}).get('title'),
        'metrics': data.get('metrics_summary', {}),
        'df_dict': data.get('df_dict', {}),
        'trend_dict': data.get('trend_dict', {}),
        'sentiment_counts': data.get('sentiment_counts', {}),
        'fraud_threshold': data.get('fraud_threshold'),
        'all_text': data.get('all_text', '')
    }
    if fs_save_result(current_user.id, result_data):
        flash('Analysis saved successfully', 'success')
    else:
        flash('Failed to save analysis', 'danger')
    return redirect(url_for('auth.dashboard'))

@main_bp.route('/send_email_report', methods=['POST'])
def send_email_report():
    """Send analysis report via email with quota enforcement for anonymous and registered users."""
    recipient_email = request.form.get('recipient_email', '').strip()
    if not recipient_email or 'last_analysis_file' not in session:
        flash('Invalid request.', 'danger')
        return redirect(url_for('main.index'))

    # Load analysis
    analysis_path = os.path.join(Config.RESULTS_FOLDER, session['last_analysis_file'])
    try:
        with open(analysis_path, 'r') as f:
            data = json.load(f)
    except Exception:
        flash('Failed to load analysis data', 'danger')
        return redirect(url_for('main.index'))

    # Prepare attachments
    df = pd.DataFrame.from_dict(data.get('df_dict', {}))
    csv_bytes = df[['at', 'content', 'sentiment', 'polarity']].to_csv(index=False).encode('utf-8') if not df.empty else b''
    trend_df = pd.DataFrame.from_dict(data.get('trend_dict', {}))
    classification_metrics = data.get('classification_metrics', None)
    pdf_buffer = generate_single_app_pdf_report(
        data['app_id'], data.get('app_details', {}), df, pd.Series(data.get('sentiment_counts', {})),
        data.get('metrics_summary', {}).get('positive_pct', 0.0),
        data.get('metrics_summary', {}).get('negative_pct', 0.0),
        data.get('metrics_summary', {}).get('neutral_pct', 0.0) if data.get('metrics_summary') else 0.0,
        data.get('metrics_summary', {}).get('app_rating_score', 0.0),
        data.get('playstore_score', 0.0) if data.get('playstore_score') else 0.0,
        data.get('fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD),
        trend_df, data.get('all_text', ''), pd.DataFrame(), classification_metrics
    )

    # Quota enforcement
    from file_store import can_user_send_email, increment_user_email_counters

    # Anonymous users: per-session limit of 3
    if not current_user.is_authenticated:
        anon_count = session.get('anon_email_sent_count', 0)
        if anon_count >= 3:
            flash('Anonymous users can send up to 3 email reports. Please sign up to send more.', 'warning')
            return redirect(request.referrer or url_for('main.index'))
        # Attempt to send email
        sent = False
        try:
            from modules.email_sender import send_analysis_email
            sent = send_analysis_email(
                user_name='Guest',
                user_email=recipient_email,
                app_details=data.get('app_details', {}),
                app_id=data.get('app_id'),
                filtered_df=df,
                sentiment_counts=pd.Series(data.get('sentiment_counts', {})),
                positive_pct=data.get('metrics_summary', {}).get('positive_pct', 0.0),
                negative_pct=data.get('metrics_summary', {}).get('negative_pct', 0.0),
                neutral_pct=data.get('metrics_summary', {}).get('neutral_pct', 0.0) if data.get('metrics_summary') else 0.0,
                app_rating_score=data.get('metrics_summary', {}).get('app_rating_score', 0.0),
                playstore_score=data.get('playstore_score', 0.0) if data.get('playstore_score') else 0.0,
                fraud_threshold=data.get('fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD),
                csv_data=csv_bytes,
                pdf_data=pdf_buffer.getvalue(),
                sender_email=Config.MAIL_USERNAME,
                sender_password=Config.MAIL_PASSWORD,
                smtp_server=Config.MAIL_SERVER,
                smtp_port=Config.MAIL_PORT
            )
        except Exception:
            sent = False

        if sent:
            session['anon_email_sent_count'] = anon_count + 1
            flash('Email report sent successfully', 'success')
        else:
            flash('Failed to send email (SMTP may be misconfigured).', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    # Logged in users: enforce quotas
    user_id = int(current_user.id)
    user_allowed = can_user_send_email(user_id)
    if not user_allowed:
        flash('You have reached your email sending limit. Contact admin for verification or wait until quota resets.', 'warning')
        return redirect(request.referrer or url_for('main.index'))

    # Send email for logged-in user
    sent = False
    try:
        from modules.email_sender import send_analysis_email
        user_info = get_user_by_id(user_id)
        sent = send_analysis_email(
            user_name=user_info.get('username', ''),
            user_email=recipient_email,
            app_details=data.get('app_details', {}),
            app_id=data.get('app_id'),
            filtered_df=df,
            sentiment_counts=pd.Series(data.get('sentiment_counts', {})),
            positive_pct=data.get('metrics_summary', {}).get('positive_pct', 0.0),
            negative_pct=data.get('metrics_summary', {}).get('negative_pct', 0.0),
            neutral_pct=data.get('metrics_summary', {}).get('neutral_pct', 0.0) if data.get('metrics_summary') else 0.0,
            app_rating_score=data.get('metrics_summary', {}).get('app_rating_score', 0.0),
            playstore_score=data.get('playstore_score', 0.0) if data.get('playstore_score') else 0.0,
            fraud_threshold=data.get('fraud_threshold', Config.DEFAULT_FRAUD_THRESHOLD),
            csv_data=csv_bytes,
            pdf_data=pdf_buffer.getvalue(),
            sender_email=Config.MAIL_USERNAME,
            sender_password=Config.MAIL_PASSWORD,
            smtp_server=Config.MAIL_SERVER,
            smtp_port=Config.MAIL_PORT
        )
    except Exception:
        sent = False

    if sent:
        increment_user_email_counters(user_id)
        flash('Email report sent successfully', 'success')
    else:
        flash('Failed to send email (SMTP may be misconfigured).', 'danger')
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/clear_search')
def clear_search():
    session['search_results'] = []
    session['show_search_results'] = False
    return redirect(url_for('main.index'))