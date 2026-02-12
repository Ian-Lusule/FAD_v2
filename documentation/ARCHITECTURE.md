# System Architecture Documentation

## Overview

The Fraud App Analyzer is built on a modular, layered architecture following the MVC (Model-View-Controller) pattern adapted for Flask's blueprint system. The application uses a file-based storage system for simplicity and portability.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│              (Browser - Bootstrap 5 + JavaScript)                │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/HTTP
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx Reverse Proxy                         │
│                    (SSL Termination, Static)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP (localhost:5001)
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Gunicorn WSGI Server                        │
│                      (3 Worker Processes)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Application                           │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Auth BP   │  │   Main BP   │  │  Admin BP   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                 │                 │                    │
│         └─────────────────┴─────────────────┘                    │
│                           │                                       │
│         ┌─────────────────┴─────────────────┐                   │
│         │      Application Core              │                   │
│         │  - Session Management              │                   │
│         │  - Authentication/Authorization    │                   │
│         │  - Request/Response Handling       │                   │
│         └─────────────────┬─────────────────┘                   │
│                           │                                       │
│         ┌─────────────────┴─────────────────┐                   │
│         │       Business Logic Modules        │                   │
│         │  ┌──────────────────────────────┐  │                   │
│         │  │   data_fetcher.py            │  │                   │
│         │  │   (Google Play Scraping)     │  │                   │
│         │  └──────────────┬───────────────┘  │                   │
│         │  ┌──────────────┴───────────────┐  │                   │
│         │  │   sentiment_analyzer.py      │  │                   │
│         │  │   (NLP & ML Classification)  │  │                   │
│         │  └──────────────┬───────────────┘  │                   │
│         │  ┌──────────────┴───────────────┐  │                   │
│         │  │   report_generator.py        │  │                   │
│         │  │   (PDF & Visualization)      │  │                   │
│         │  └──────────────┬───────────────┘  │                   │
│         │  ┌──────────────┴───────────────┐  │                   │
│         │  │   email_sender.py            │  │                   │
│         │  │   (SMTP Email Delivery)      │  │                   │
│         │  └──────────────────────────────┘  │                   │
│         └─────────────────┬─────────────────┘                   │
│                           │                                       │
│         ┌─────────────────┴─────────────────┐                   │
│         │       Data Access Layer           │                   │
│         │       (file_store.py)             │                   │
│         └─────────────────┬─────────────────┘                   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ↓
        ┌───────────────────────────────────────┐
        │       File System Storage              │
        │  - users.json                          │
        │  - messages.json                       │
        │  - search_logs.csv                     │
        │  - results/*.json                      │
        │  - flask_session/*                     │
        └───────────────────────────────────────┘
```

## Component Layers

### 1. Presentation Layer

**Technology**: HTML5, Bootstrap 5, JavaScript, Jinja2 Templates

**Components**:
- **Templates** (`/templates`): Jinja2 HTML templates
  - Base template with navigation and layout
  - Feature-specific templates (auth, analysis, admin)
  - Responsive design for mobile/desktop

- **Static Assets** (`/static`):
  - CSS: Custom styles, Bootstrap overrides
  - JavaScript: Client-side form validation, dynamic updates

**Responsibilities**:
- Render HTML responses
- Handle user input and validation
- Display flash messages and errors
- Provide interactive UI components

### 2. Application Layer

**Technology**: Flask, Flask-Login, Flask-Session, Flask-Mail

**Components**:

#### Blueprints

| Blueprint | Prefix | Purpose | Key Routes |
|-----------|--------|---------|------------|
| `auth_bp` | `/auth` | Authentication & user management | `/login`, `/register`, `/dashboard` |
| `main_bp` | `/` | Core application logic | `/`, `/analyze`, `/results`, `/compare` |
| `admin_bp` | `/admin` | Admin functionality | `/dashboard`, `/users`, `/messages` |
| `filters_bp` | N/A | Custom Jinja2 filters | N/A |

#### Core Services

**Session Management**:
```python
SESSION_TYPE='filesystem'  # Server-side sessions
SESSION_FILE_DIR='./flask_session'
SESSION_PERMANENT=False
SESSION_USE_SIGNER=True
```

**Authentication System**:
- Flask-Login for session management
- Werkzeug password hashing (PBKDF2)
- Role-based access control (admin/user)

**Email Service**:
- Flask-Mail with SMTP support
- Async-friendly with config fallback
- Supports SSL/TLS and STARTTLS

### 3. Business Logic Layer

**Technology**: Python, Pandas, TextBlob, scikit-learn, Matplotlib, ReportLab

**Modules**:

#### `data_fetcher.py`
```python
Purpose: Google Play Store data acquisition
Dependencies: google-play-scraper, requests
Key Functions:
  - search_apps(query, country, count)
  - fetch_app_details(app_id, country)
  - fetch_reviews(app_id, country, count)
```

#### `sentiment_analyzer.py`
```python
Purpose: NLP sentiment analysis and ML classification
Dependencies: TextBlob, scikit-learn, pandas
Key Functions:
  - analyze_sentiment(reviews) → DataFrame
  - calculate_sentiment_metrics(df) → dict
  - perform_ml_classification(df) → dict with confusion matrix
```

#### `report_generator.py`
```python
Purpose: PDF report generation and visualization
Dependencies: ReportLab, Matplotlib, WordCloud
Key Functions:
  - generate_single_app_pdf_report(data) → BytesIO
  - create_sentiment_trend_chart(df) → Figure
  - create_word_cloud_image(text) → Figure
```

#### `email_sender.py`
```python
Purpose: Email delivery with attachments
Dependencies: smtplib, email.mime
Key Functions:
  - send_analysis_email(to, subject, html, attachments)
```

### 4. Data Access Layer

**Technology**: JSON file storage, CSV logging

**Component**: `file_store.py`

**Storage Schema**:

```python
# User Management
- create_user(username, email, password)
- get_user_by_username(username)
- get_all_users()
- update_user(user_id, updates)
- delete_user(user_id)

# Analysis Results
- save_result(user_id, app_id, data)
- get_user_results(user_id)
- delete_result(result_id)

# Messaging
- add_message(user_id, subject, message, sender)
- get_user_messages(user_id)
- mark_message_as_read(message_id)

# Analytics
- append_search_log(user_id, username, app_id, ...)
- get_search_logs()
```

## Data Flow Diagrams

### Analysis Request Flow

```
1. User submits app ID/URL
   ↓
2. main.py:analyze() validates input
   ↓
3. data_fetcher.fetch_app_details() → App metadata
   ↓
4. data_fetcher.fetch_reviews() → Reviews (up to 5000)
   ↓
5. sentiment_analyzer.analyze_sentiment() → Sentiment labels
   ↓
6. sentiment_analyzer.perform_ml_classification() → Risk metrics
   ↓
7. file_store.save_result() → JSON file
   ↓
8. file_store.append_search_log() → CSV log
   ↓
9. Render results.html with data
```

### PDF Export Flow

```
1. User clicks "Download PDF"
   ↓
2. main.py:export_pdf() retrieves analysis data
   ↓
3. report_generator.generate_single_app_pdf_report()
   ├─→ create_sentiment_trend_chart() → Matplotlib figure
   ├─→ create_word_cloud_image() → WordCloud figure
   └─→ ReportLab: Assemble PDF with charts and tables
   ↓
4. Return BytesIO buffer as download
```

### Email Delivery Flow

```
1. User clicks "Send Email"
   ↓
2. main.py:send_email_report() generates PDF
   ↓
3. email_sender.send_analysis_email()
   ├─→ Build multipart MIME message
   ├─→ Attach PDF and CSV files
   ├─→ Connect to SMTP server (SSL/TLS)
   └─→ Send email
   ↓
4. Flash success/error message
```

## Security Architecture

### Authentication & Authorization

```
┌──────────────────────────────────────────────┐
│         Unauthenticated Request              │
└──────────────────┬───────────────────────────┘
                   ↓
         ┌─────────────────────┐
         │  @login_required    │
         │  decorator          │
         └──────┬──────────────┘
                ↓
         ┌─────────────────────┐
         │  Flask-Login        │
         │  session check      │
         └──────┬──────────────┘
                ↓
        [User authenticated?]
         ┌──────┴──────┐
         NO            YES
         │              │
         ↓              ↓
    Redirect to    Check role
    /auth/login    (if needed)
                        │
                        ↓
               [Admin required?]
                ┌──────┴──────┐
                NO            YES
                │              │
                ↓              ↓
           Allow access   Check is_admin
                               │
                               ↓
                       [Is admin?]
                        ┌─────┴─────┐
                        NO          YES
                        │            │
                        ↓            ↓
                    403 Error   Allow access
```

### Password Security

```python
Registration/Password Change:
1. Validate password strength (8+ chars, complexity)
2. Hash with Werkzeug (PBKDF2-SHA256, salt)
3. Store only hash (never plaintext)

Login:
1. Retrieve user by username
2. check_password_hash(stored_hash, input_password)
3. Create session if valid
```

### Session Management

```python
- Session storage: Server-side (filesystem)
- Session signing: SECRET_KEY (cryptographic signature)
- Session timeout: 1 hour (configurable)
- Cookie flags: HttpOnly, Secure (HTTPS only)
```

## Deployment Architecture

### Production Stack

```
Internet
   │
   ↓ [Port 80/443]
┌────────────────┐
│   Firewall/    │ ← UFW/iptables rules
│  Cloud Sec Grp │    Allow: 22, 80, 443
└───────┬────────┘
        │
        ↓
┌────────────────┐
│     Nginx      │ ← Reverse proxy + SSL termination
│   (Port 80/443)│    + Static file serving
└───────┬────────┘
        │ proxy_pass http://127.0.0.1:5001
        ↓
┌────────────────┐
│   Gunicorn     │ ← WSGI server (3 workers)
│  (127.0.0.1:   │    Bind to localhost only
│     5001)      │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│  Flask App     │ ← Application code
│  (Python 3.8)  │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│  File System   │ ← Data storage
│  (/data, /logs)│
└────────────────┘
```

### Service Management

```
systemd (fraud-app.service)
   ├─→ Manages Gunicorn process lifecycle
   ├─→ Auto-restart on failure
   ├─→ Logs to journald
   └─→ Environment from /path/to/project/.env

Nginx
   ├─→ Managed by systemd (nginx.service)
   ├─→ Config: /etc/nginx/conf.d/domains/faa.shule.com.conf
   └─→ SSL Certs: /etc/letsencrypt/live/faa.shule.com/

Certbot
   ├─→ Automated SSL certificate renewal
   ├─→ Systemd timer: certbot.timer
   └─→ Webroot validation via Nginx
```

## Scalability Considerations

### Current Limitations

- **Storage**: File-based (JSON/CSV) - not suitable for high concurrency
- **Session**: Filesystem sessions - no cross-server sharing
- **Workers**: 3 Gunicorn workers - limited concurrent requests
- **Caching**: No caching layer implemented

### Recommended Upgrades for Scale

```
┌─────────────────────────────────────────────────┐
│  Load Balancer (HAProxy/Nginx)                  │
└──────────┬──────────────┬────────────────┬──────┘
           │              │                │
    ┌──────┴─────┐ ┌──────┴─────┐  ┌──────┴─────┐
    │  App       │ │  App       │  │  App       │
    │  Server 1  │ │  Server 2  │  │  Server N  │
    └──────┬─────┘ └──────┬─────┘  └──────┬─────┘
           │              │                │
           └──────────────┴────────────────┘
                          │
                ┌─────────┴──────────┐
                │                    │
        ┌───────┴─────────┐  ┌──────┴────────┐
        │  PostgreSQL/    │  │  Redis        │
        │  MySQL          │  │  (Sessions &  │
        │  (Primary DB)   │  │   Cache)      │
        └─────────────────┘  └───────────────┘
```

## Performance Optimization

### Current Optimizations

1. **Matplotlib Backend**: Non-interactive (`Agg`) to avoid threading issues
2. **ReportLab Patch**: Monkey-patch for Python 3.8 + OpenSSL 3 compatibility
3. **Session Storage**: Server-side to reduce cookie size
4. **Static Files**: Served directly by Nginx (bypass Flask)
5. **Gunicorn Workers**: Multiple workers for parallel request handling

### Bottlenecks

1. **Google Play Scraper**: Rate-limited, synchronous API calls
2. **ML Classification**: CPU-intensive scikit-learn operations
3. **PDF Generation**: Memory-intensive for large reports
4. **File I/O**: JSON read/write for every user/result operation

## Error Handling Strategy

```python
Application Level:
├─→ Try/Except blocks around external API calls
├─→ Graceful degradation (show partial results on errors)
├─→ Flash messages for user-facing errors
└─→ Logging to stdout (captured by systemd)

Infrastructure Level:
├─→ Gunicorn: Auto-restart workers on crash
├─→ Systemd: Auto-restart service on failure
├─→ Nginx: Returns 502 if upstream unavailable
└─→ Certbot: Auto-renew certs with email alerts
```

---

**Design Principles**:
- **Modularity**: Clear separation of concerns across modules
- **Simplicity**: File-based storage for easy deployment
- **Security**: Password hashing, session management, HTTPS
- **Maintainability**: Blueprint structure, documented code
- **Portability**: Minimal external dependencies, containerizable

**Last Updated**: February 2026
