# File Structure Documentation

## Project Directory Tree

```
fraud-app-analyzer-flask/
├── app.py                          # Application factory and initialization
├── run.py                          # Development server entry point
├── wsgi.py                         # Production WSGI entry point
├── config.py                       # Configuration management
├── auth.py                         # Authentication blueprint and User model
├── admin.py                        # Admin dashboard blueprint
├── main.py                         # Main application routes blueprint
├── filters.py                      # Custom Jinja2 template filters
├── file_store.py                   # File-based data storage layer
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (not in git)
├── README.md                       # Project readme
├── reportlab_patch.py              # Monkey-patch for ReportLab/OpenSSL compatibility
│
├── modules/                        # Analysis and processing modules
│   ├── __init__.py
│   ├── data_fetcher.py            # Google Play Store data scraping
│   ├── sentiment_analyzer.py     # Sentiment analysis and ML classification
│   ├── report_generator.py       # PDF report generation
│   └── email_sender.py            # Email delivery system
│
├── static/                         # Static assets (CSS, JS, images)
│   ├── css/
│   │   └── style.css             # Main stylesheet
│   └── js/
│       └── main.js               # Client-side JavaScript
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                 # Base template with navigation
│   ├── index.html                # Landing page
│   ├── error.html                # Error page template
│   │
│   ├── auth/                     # Authentication templates
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html        # User dashboard
│   │   ├── change_password.html
│   │   └── contact_admin.html
│   │
│   ├── analysis/                 # Analysis templates
│   │   ├── results.html          # Single app analysis results
│   │   └── compare.html          # Multi-app comparison
│   │
│   └── admin/                    # Admin templates
│       ├── dashboard.html        # Admin overview
│       ├── users.html            # User management
│       ├── messages.html         # Message center
│       └── analytics.html        # Usage analytics
│
├── data/                           # Application data storage
│   ├── users.json                # User accounts database
│   ├── messages.json             # User messages and notifications
│   ├── search_logs.csv           # Search history and analytics
│   └── results/                  # Saved analysis results (JSON)
│       └── *.json
│
├── flask_session/                  # Server-side session storage
│
├── documentation/                  # Project documentation
│   ├── README.md                 # Documentation index
│   ├── ARCHITECTURE.md           # System architecture
│   ├── INSTALLATION.md           # Installation guide
│   ├── API.md                    # API reference
│   ├── DATABASE.md               # Data models
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── CONFIGURATION.md          # Configuration reference
│   ├── TROUBLESHOOTING.md        # Issue resolution
│   ├── DEVELOPMENT.md            # Developer guide
│   ├── FILE_STRUCTURE.md         # This file
│   └── AI_PROMPT.md              # AI documentation template
│
└── Install on Hestia oracle server.sh  # Automated production installer

```

## Core Application Files

### Application Entry Points

| File | Purpose | Key Components |
|------|---------|----------------|
| `app.py` | Flask application factory | `create_app()`, extension initialization, blueprint registration |
| `run.py` | Development server | Direct Flask server for local dev |
| `wsgi.py` | Production WSGI interface | Gunicorn entry point with ReportLab patch |

### Configuration & Setup

| File | Purpose | Key Components |
|------|---------|----------------|
| `config.py` | Configuration management | `Config` class, environment variable loading |
| `.env` | Environment variables | SECRET_KEY, MAIL_*, admin credentials |
| `requirements.txt` | Python dependencies | Flask, Pandas, TextBlob, ReportLab, etc. |

### Core Blueprints

| File | Purpose | Routes | Key Functions |
|------|---------|--------|---------------|
| `auth.py` | Authentication system | `/auth/login`, `/auth/register`, `/auth/dashboard` | User login, registration, password management |
| `admin.py` | Admin functionality | `/admin/dashboard`, `/admin/users`, `/admin/messages` | User management, analytics, messaging |
| `main.py` | Main application logic | `/`, `/analyze`, `/results`, `/compare`, `/export/*` | App analysis, result display, exports |
| `filters.py` | Template filters | N/A | Custom Jinja2 filters for date formatting, etc. |

### Data Layer

| File | Purpose | Key Functions |
|------|---------|---------------|
| `file_store.py` | File-based database | `create_user()`, `save_result()`, `append_search_log()`, `load_messages()` |

## Module Breakdown

### `/modules/` Directory

| Module | Purpose | Key Functions | Dependencies |
|--------|---------|---------------|--------------|
| `data_fetcher.py` | Google Play scraping | `search_apps()`, `fetch_app_details()`, `fetch_reviews()` | google-play-scraper |
| `sentiment_analyzer.py` | NLP and ML | `analyze_sentiment()`, `calculate_sentiment_metrics()`, `perform_ml_classification()` | TextBlob, scikit-learn, Pandas |
| `report_generator.py` | PDF generation | `generate_single_app_pdf_report()`, `create_sentiment_trend_chart()`, `create_word_cloud_image()` | ReportLab, Matplotlib, WordCloud |
| `email_sender.py` | Email delivery | `send_analysis_email()` | smtplib, email |

### Module Dependencies Graph

```
data_fetcher.py  ──┐
                   ├──> main.py ──> templates/analysis/*.html
sentiment_analyzer ─┤
                   │
report_generator ──┼──> email_sender.py
                   │
file_store.py ─────┘
```

## Template Structure

### Template Hierarchy

```
base.html (navigation, flash messages, common layout)
  │
  ├── index.html (landing page, search form)
  │
  ├── auth/
  │   ├── login.html
  │   ├── register.html
  │   └── dashboard.html (user's saved analyses)
  │
  ├── analysis/
  │   ├── results.html (single app analysis display)
  │   └── compare.html (multi-app comparison)
  │
  ├── admin/
  │   ├── dashboard.html (admin overview)
  │   ├── users.html (user management interface)
  │   ├── messages.html (message center)
  │   └── analytics.html (usage statistics)
  │
  └── error.html (error display)
```

### Template Blocks

Each template extends `base.html` and can override:
- `{% block title %}` - Page title
- `{% block content %}` - Main content area
- Additional CSS/JS can be added inline

## Data Storage Structure

### `/data/` Directory

#### `users.json`
```json
[
  {
    "id": 1,
    "username": "string",
    "email": "string",
    "password_hash": "string",
    "is_admin": boolean,
    "is_main_admin": boolean,
    "created_at": "ISO8601 timestamp",
    "last_login": "ISO8601 timestamp"
  }
]
```

#### `messages.json`
```json
[
  {
    "id": 1,
    "user_id": integer,
    "subject": "string",
    "message": "string",
    "timestamp": "ISO8601 timestamp",
    "read": boolean,
    "sender": "string"
  }
]
```

#### `search_logs.csv`
```csv
timestamp,user_id,username,app_id,app_name,country,num_reviews
2026-02-12 10:30:00,1,john_doe,com.example.app,Example App,us,100
```

#### `/data/results/*.json`
Analysis result files named: `{user_id}_{timestamp}_{app_id}.json`

```json
{
  "app_id": "string",
  "app_name": "string",
  "developer": "string",
  "score": float,
  "reviews_analyzed": integer,
  "sentiment_counts": {...},
  "classification_metrics": {...},
  "reviews": [...],
  "timestamp": "ISO8601 timestamp"
}
```

## Static Assets

### `/static/css/`
- `style.css` - Main application styles (Bootstrap overrides, custom components)

### `/static/js/`
- `main.js` - Client-side interactions, form handling, dynamic updates

## Configuration Files

### Environment Files
- `.env` - Local development configuration
- `.env.example` - Template for required environment variables

### Deployment Files
- `Install on Hestia oracle server.sh` - Automated production installer
  - Creates systemd service
  - Configures Nginx with SSL
  - Sets up firewall rules
  - Runs certbot for HTTPS

### System Integration
- `/etc/systemd/system/fraud-app.service` - Systemd service definition
- `/etc/nginx/conf.d/domains/faa.shule.com.conf` - Nginx configuration
- `/etc/letsencrypt/live/faa.shule.com/` - SSL certificates

## Key File Relationships

### Analysis Workflow
```
User Input → main.py:analyze()
              ↓
         data_fetcher.py:fetch_app_details()
         data_fetcher.py:fetch_reviews()
              ↓
         sentiment_analyzer.py:analyze_sentiment()
         sentiment_analyzer.py:perform_ml_classification()
              ↓
         file_store.py:save_result()
              ↓
         main.py:results() → templates/analysis/results.html
```

### PDF Export Workflow
```
User clicks "Download PDF" → main.py:export_pdf()
                              ↓
                         report_generator.py:generate_single_app_pdf_report()
                              ↓
                         matplotlib (charts)
                         wordcloud (visualization)
                         ReportLab (PDF assembly)
                              ↓
                         send_file() → User browser
```

### Email Workflow
```
User clicks "Send Email" → main.py:send_email_report()
                            ↓
                       report_generator.py:generate_single_app_pdf_report()
                            ↓
                       email_sender.py:send_analysis_email()
                            ↓
                       SMTP server → Recipient inbox
```

## File Naming Conventions

### Python Files
- `snake_case.py` for module names
- Blueprint files match their blueprint name (e.g., `auth.py` for `auth_bp`)

### Templates
- `lowercase.html` with descriptive names
- Organized by feature in subdirectories

### Data Files
- JSON files: `{entity_name}.json`
- Results: `{user_id}_{timestamp}_{app_id}.json`
- Logs: `{log_type}_logs.csv`

### Configuration
- `.env` for environment-specific settings
- `config.py` for application configuration class

---

**Note**: Files marked with `(not in git)` should be excluded from version control via `.gitignore`.

**Last Updated**: February 2026
