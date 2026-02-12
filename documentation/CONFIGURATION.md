# Configuration Guide

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Config.py Settings](#configpy-settings)
3. [Gunicorn Configuration](#gunicorn-configuration)
4. [Nginx Configuration](#nginx-configuration)
5. [Systemd Service Configuration](#systemd-service-configuration)
6. [Email Configuration](#email-configuration)
7. [Security Configuration](#security-configuration)
8. [Performance Tuning](#performance-tuning)

---

## Environment Variables

All environment variables are stored in `.env` file in the project root.

### Required Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `SECRET_KEY` | Flask session encryption key | `a1b2c3d4...` | None (must set) |
| `ADMIN_USERNAME` | Default admin username | `admin` | None |
| `ADMIN_EMAIL` | Default admin email | `admin@example.com` | None |
| `ADMIN_PASSWORD` | Default admin password | `SecurePass123!` | None |

### Optional Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `FLASK_ENV` | Environment mode | `production` or `development` | `production` |
| `DEBUG` | Enable debug mode | `True` or `False` | `False` |
| `PORT` | Development server port | `5000` | `5000` |
| `HOST` | Development server host | `0.0.0.0` | `127.0.0.1` |

### Email Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `MAIL_SERVER` | SMTP server hostname | `smtp.gmail.com` | None |
| `MAIL_PORT` | SMTP server port | `587` (TLS) or `465` (SSL) | None |
| `MAIL_USE_TLS` | Use STARTTLS | `True` or `False` | Auto-detect |
| `MAIL_USE_SSL` | Use SSL/TLS | `True` or `False` | Auto-detect |
| `MAIL_USERNAME` | SMTP username | `noreply@example.com` | None |
| `MAIL_PASSWORD` | SMTP password/app password | `app-password` | None |

**Email Port Rules**:
- Port **587**: Uses STARTTLS (`MAIL_USE_TLS=True`)
- Port **465**: Uses SSL/TLS (`MAIL_USE_SSL=True`)
- Port **25**: Plain (not recommended)

### Example .env File

**Production**:
```bash
# Application
SECRET_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
FLASK_ENV=production
DEBUG=False

# Admin Account
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=YourSecurePassword123!

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-google-app-password
```

**Development**:
```bash
# Application
SECRET_KEY=dev-secret-key-change-me
FLASK_ENV=development
DEBUG=True
PORT=5000
HOST=0.0.0.0

# Admin Account
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@localhost
ADMIN_PASSWORD=admin123

# Email (optional for dev)
MAIL_SERVER=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-user
MAIL_PASSWORD=your-mailtrap-pass
```

### Generating SECRET_KEY

```bash
# Method 1: Using Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Method 2: Using OpenSSL
openssl rand -hex 32

# Method 3: Using /dev/urandom
head -c 32 /dev/urandom | base64
```

---

## Config.py Settings

Located at [config.py](../config.py)

### Core Settings

```python
class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = './flask_session'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security
    SESSION_COOKIE_SECURE = True   # HTTPS only
    SESSION_COOKIE_HTTPONLY = True  # No JS access
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### Email Settings

```python
# SMTP Configuration
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
```

### File Storage Settings

```python
# Data directories
DATA_DIR = 'data'
RESULTS_DIR = 'data/results'
USERS_FILE = 'data/users.json'
MESSAGES_FILE = 'data/messages.json'
SEARCH_LOGS_FILE = 'data/search_logs.csv'
```

### Customizing Config

**1. Edit config.py directly** (for global changes):
```python
class Config:
    # Increase session lifetime
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Change upload limit
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
```

**2. Use environment variables** (for deployment-specific):
```bash
# .env
SESSION_LIFETIME_DAYS=30
MAX_UPLOAD_MB=32
```

Then update config.py:
```python
PERMANENT_SESSION_LIFETIME = timedelta(
    days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7))
)
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', 16)) * 1024 * 1024
```

---

## Gunicorn Configuration

### Command-Line Options (systemd)

Located in `/etc/systemd/system/fraud-app.service`:

```ini
ExecStart=/path/to/venv/bin/gunicorn \
    -w 3 \                          # Workers
    -b 127.0.0.1:5001 \            # Bind address
    --timeout 120 \                 # Request timeout (seconds)
    --max-requests 1000 \           # Restart after N requests
    --max-requests-jitter 50 \      # Random jitter
    --access-logfile /var/log/fraud-app/access.log \
    --error-logfile /var/log/fraud-app/error.log \
    --log-level info \
    wsgi:app
```

### Configuration File (gunicorn_config.py)

Alternative method - create `gunicorn_config.py`:

```python
import multiprocessing

# Server socket
bind = "127.0.0.1:5001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Request limits
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '/var/log/fraud-app/access.log'
errorlog = '/var/log/fraud-app/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'fraud-app'

# Server mechanics
daemon = False
pidfile = '/tmp/fraud-app.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'
```

Then update systemd ExecStart:
```ini
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
```

### Worker Calculation

```python
# Rule of thumb
workers = (2 * CPU_CORES) + 1

# For CPU-intensive tasks (like PDF generation)
workers = CPU_CORES + 1

# Check CPU cores
import multiprocessing
print(multiprocessing.cpu_count())
```

**Examples**:
- 2 cores → 3-5 workers
- 4 cores → 5-9 workers
- 8 cores → 9-17 workers

### Timeout Settings

| Task | Recommended Timeout |
|------|---------------------|
| Simple requests | 30s |
| Analysis (scraping) | 60-90s |
| PDF generation | 90-120s |
| Large WordCloud | 120-180s |

**Current setting**: 120s (good for most operations)

---

## Nginx Configuration

### HTTP → HTTPS Redirect

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Allow certbot validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect everything else to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}
```

### HTTPS Server Block

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Gunicorn
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:5001;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }
    
    # Static files (optional optimization)
    location /static/ {
        alias /path/to/fraud-app-analyzer-flask/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Logging
    access_log /var/log/nginx/fraud-app_access.log;
    error_log /var/log/nginx/fraud-app_error.log;
}
```

### Hestia-Specific Configuration

When using Hestia Control Panel, add explicit listen directives:

```nginx
server {
    # Explicit IP binding (override Hestia defaults)
    listen 10.0.0.205:80;
    listen [::]:80;
    
    server_name yourdomain.com www.yourdomain.com;
    # ... rest of config
}

server {
    # Explicit IP binding for HTTPS
    listen 10.0.0.205:443 ssl http2;
    listen [::]:443 ssl http2;
    
    server_name yourdomain.com www.yourdomain.com;
    # ... rest of config
}
```

### Rate Limiting

```nginx
# In http block
limit_req_zone $binary_remote_addr zone=app_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# In server block
location / {
    limit_req zone=app_limit burst=20 nodelay;
    # ... proxy config
}

location /auth/login {
    limit_req zone=login_limit burst=3 nodelay;
    # ... proxy config
}
```

---

## Systemd Service Configuration

File: `/etc/systemd/system/fraud-app.service`

### Basic Configuration

```ini
[Unit]
Description=Gunicorn instance serving Fraud App Analyzer
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=fraudapp
Group=fraudapp
WorkingDirectory=/home/fraudapp/fraud-app-analyzer-flask

# Environment
Environment="PATH=/home/fraudapp/fraud-app-analyzer-flask/venv/bin"
EnvironmentFile=-/home/fraudapp/fraud-app-analyzer-flask/.env

# Execution
ExecStart=/home/fraudapp/fraud-app-analyzer-flask/venv/bin/gunicorn \
    -w 3 \
    -b 127.0.0.1:5001 \
    --timeout 120 \
    wsgi:app

# Restart policy
Restart=always
RestartSec=3
StartLimitInterval=300
StartLimitBurst=5

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/fraudapp/fraud-app-analyzer-flask/data
ReadWritePaths=/home/fraudapp/fraud-app-analyzer-flask/flask_session

[Install]
WantedBy=multi-user.target
```

### Advanced Security

```ini
[Service]
# Sandboxing
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/fraudapp/fraud-app-analyzer-flask/data
ReadWritePaths=/home/fraudapp/fraud-app-analyzer-flask/flask_session
ReadWritePaths=/var/log/fraud-app

# Capabilities
CapabilityBoundingSet=
AmbientCapabilities=
NoNewPrivileges=true

# System call filtering
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# Network
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# Devices
PrivateDevices=true
DevicePolicy=closed

# Kernel
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
LimitNOFILE=4096
LimitNPROC=512
```

### Reload Configuration

```bash
# After editing service file
sudo systemctl daemon-reload
sudo systemctl restart fraud-app
sudo systemctl status fraud-app
```

---

## Email Configuration

### Gmail Setup

1. **Enable 2FA**: https://myaccount.google.com/security
2. **Create App Password**: https://myaccount.google.com/apppasswords
3. **Configure .env**:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

### Office 365 / Outlook

```bash
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

### Custom SMTP Server

```bash
# TLS (port 587)
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-password

# SSL (port 465)
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-password
```

### Testing Email

```bash
# Python test script
python3 << 'EOF'
import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

with app.app_context():
    msg = Message('Test Email', recipients=['test@example.com'])
    msg.body = 'This is a test email from Fraud App Analyzer'
    mail.send(msg)
    print("Email sent successfully!")
EOF
```

---

## Security Configuration

### Session Security

```python
# config.py
SESSION_COOKIE_SECURE = True       # HTTPS only
SESSION_COOKIE_HTTPONLY = True     # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

### Password Hashing

Uses Werkzeug's `generate_password_hash` with default params:
- Method: `pbkdf2:sha256`
- Salt length: 16 bytes
- Iterations: 260,000

**Custom settings** (in auth.py if needed):
```python
from werkzeug.security import generate_password_hash

hashed = generate_password_hash(
    password,
    method='pbkdf2:sha256:600000',  # More iterations
    salt_length=32                   # Longer salt
)
```

### HTTPS/TLS Configuration

See [Nginx Configuration](#nginx-configuration) SSL settings.

**Minimum TLS version**: TLSv1.2
**Recommended**: TLSv1.3 only (if supported by clients)

```nginx
ssl_protocols TLSv1.3;
```

### File Upload Security

```python
# config.py
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

# Validate file types (if implementing file uploads)
ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

---

## Performance Tuning

### Gunicorn Workers

```bash
# CPU-bound (PDF generation, analysis)
workers = CPU_CORES + 1

# I/O-bound (network requests, database)
workers = (CPU_CORES * 2) + 1
```

### Nginx Caching

```nginx
# Cache static files
location /static/ {
    alias /path/to/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Cache analysis results (if applicable)
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m inactive=60m;
proxy_cache_key "$scheme$request_method$host$request_uri";

location /analysis/ {
    proxy_cache app_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_use_stale error timeout updating;
    # ... rest of proxy config
}
```

### Database Optimization

**JSON file caching** (if needed):
```python
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def load_users_cached():
    return load_users()

# Invalidate cache after writes
def save_users(users):
    # ... save logic
    load_users_cached.cache_clear()
```

### Log Rotation

See [INSTALLATION.md](INSTALLATION.md#post-installation-configuration) for logrotate setup.

---

**Last Updated**: February 2026
