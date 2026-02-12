# Installation Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Automated Installation (Hestia/Oracle)](#automated-installation)
5. [Manual Production Setup](#manual-production-setup)
6. [Post-Installation Configuration](#post-installation-configuration)
7. [Verification](#verification)

---

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Linux (Ubuntu 20.04+, Debian 11+, Oracle Linux 8+, CentOS 8+) |
| **Python** | 3.8 or higher |
| **RAM** | 2GB minimum, 4GB recommended |
| **Storage** | 2GB free space minimum |
| **Network** | Outbound HTTPS access to play.google.com |

### Software Dependencies

**System Packages**:
- `python3` (3.8+)
- `python3-venv`
- `python3-dev`
- `python3-pip`
- `build-essential` (gcc, make)
- `git`
- `nginx` (production only)
- `certbot` + `python3-certbot-nginx` (production HTTPS)

---

## Local Development Setup

### 1. Clone Repository

```bash
# Clone the project
git clone <repository-url>
cd fraud-app-analyzer-flask
```

### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt
```

**Note**: ReportLab requires `>=4.0.0` for Python 3.8 compatibility with OpenSSL 3.

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required `.env` variables**:
```bash
SECRET_KEY=your-secret-key-here-change-in-production
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-this-password

# Email configuration (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

**Generate SECRET_KEY**:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize Data Directory

```bash
# Create data directory structure
mkdir -p data/results

# The application will create JSON files on first run
# users.json, messages.json, search_logs.csv
```

### 6. Run Development Server

```bash
# Ensure venv is activated
source venv/bin/activate

# Run Flask development server
python run.py
```

**Output**:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://127.0.0.1:5000
```

### 7. Access Application

Open browser to: `http://localhost:5000`

**First-time setup**:
1. Register an account
2. The first registered user becomes main admin
3. Or use credentials from `.env`: `ADMIN_USERNAME` / `ADMIN_PASSWORD`

---

## Production Deployment

### Automated Installation (Hestia/Oracle)

For servers running Hestia Control Panel or Oracle Linux:

**1. Prerequisites**:
```bash
# Ensure you're root or have sudo
sudo -i

# Clone/upload project to server
cd /home/Ian-Lusule/web/your-domain.com/public_html
git clone <repository-url> fraud-app-analyzer-flask
cd fraud-app-analyzer-flask
```

**2. Edit Installer Configuration**:
```bash
nano "Install on Hestia oracle server.sh"
```

Update these variables:
```bash
DOMAIN="your-domain.com"
PROJECT_DIR="/home/Ian-Lusule/web/${DOMAIN}/public_html/fraud-app-analyzer-flask"
USER="Ian-Lusule"
GROUP="Ian-Lusule"
EMAIL_FOR_CERT="admin@your-domain.com"
```

**3. Run Installer**:
```bash
sudo bash "Install on Hestia oracle server.sh"
```

**What the installer does**:
- Installs system packages (Python, Nginx, Certbot)
- Creates Python virtual environment
- Installs Python dependencies
- Creates `wsgi.py` with ReportLab patch
- Creates systemd service (`fraud-app.service`)
- Configures Nginx reverse proxy
- Requests SSL certificate from Let's Encrypt
- Sets up firewall rules (ports 80, 443)
- Starts and enables the service

**4. Verify Installation**:
```bash
# Check service status
sudo systemctl status fraud-app

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# View logs
sudo journalctl -u fraud-app -n 50
```

**5. Access Your Site**:
- HTTP: `http://your-domain.com`
- HTTPS: `https://your-domain.com` (if SSL succeeded)

---

## Manual Production Setup

### 1. Install System Packages

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-dev python3-pip \
    nginx git lsof build-essential \
    certbot python3-certbot-nginx
```

**RHEL/CentOS/Oracle Linux**:
```bash
sudo dnf install -y \
    python3 python3-venv python3-pip \
    nginx git lsof gcc gcc-c++ make \
    certbot python3-certbot-nginx
```

### 2. Create Project User

```bash
# Create dedicated user (optional but recommended)
sudo useradd -m -s /bin/bash fraudapp
sudo passwd fraudapp

# Or use existing user
USER=youruser
```

### 3. Set Up Project

```bash
# Switch to project user
sudo su - fraudapp

# Clone repository
cd /home/fraudapp
git clone <repository-url> fraud-app-analyzer-flask
cd fraud-app-analyzer-flask

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Create .env file
nano .env
```

**Production `.env`**:
```bash
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=SecureRandomPassword123!

# Email settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=app-specific-password
```

### 5. Create ReportLab Patch

```bash
cat > reportlab_patch.py <<'EOF'
"""Monkey-patch for reportlab MD5 compatibility with Python 3.8 + OpenSSL 3"""
import hashlib

_original_md5 = hashlib.md5

def patched_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _original_md5(*args, **kwargs)

hashlib.md5 = patched_md5
EOF
```

### 6. Create WSGI Entry Point

```bash
cat > wsgi.py <<'EOF'
import reportlab_patch  # Monkey-patch MD5 for Python 3.8 + OpenSSL 3
from app import create_app

app = create_app()
EOF
```

### 7. Install Gunicorn

```bash
source venv/bin/activate
pip install gunicorn
```

### 8. Create Systemd Service

```bash
sudo nano /etc/systemd/system/fraud-app.service
```

**Service file**:
```ini
[Unit]
Description=Gunicorn instance serving Fraud App Analyzer
After=network.target

[Service]
User=fraudapp
Group=fraudapp
WorkingDirectory=/home/fraudapp/fraud-app-analyzer-flask
Environment="PATH=/home/fraudapp/fraud-app-analyzer-flask/venv/bin"
EnvironmentFile=-/home/fraudapp/fraud-app-analyzer-flask/.env
ExecStart=/home/fraudapp/fraud-app-analyzer-flask/venv/bin/gunicorn \
    -w 3 \
    -b 127.0.0.1:5001 \
    --timeout 120 \
    wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fraud-app
sudo systemctl start fraud-app
sudo systemctl status fraud-app
```

### 9. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/fraud-app
```

**Nginx configuration**:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:5001;
        proxy_read_timeout 120;
    }

    location /static/ {
        alias /home/fraudapp/fraud-app-analyzer-flask/static/;
        expires 30d;
    }
}
```

**Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/fraud-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Automatic renewal**:
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot timer is enabled by default
sudo systemctl status certbot.timer
```

### 11. Configure Firewall

**UFW (Ubuntu/Debian)**:
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

**Firewalld (RHEL/CentOS/Oracle)**:
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## Post-Installation Configuration

### 1. Create Admin Account

Visit: `https://yourdomain.com/auth/register`

Register with credentials from `.env` or create a new admin account.

### 2. Configure Email (If Not Done)

Edit `.env` with valid SMTP credentials:

**Gmail**:
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in `.env`

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
```

**Restart after changes**:
```bash
sudo systemctl restart fraud-app
```

### 3. Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/fraud-app
```

```
/var/log/fraud-app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 fraudapp fraudapp
    sharedscripts
    postrotate
        systemctl reload fraud-app
    endscript
}
```

### 4. Set Up Backups

```bash
# Backup script
sudo nano /usr/local/bin/backup-fraud-app.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/backups/fraud-app"
PROJECT_DIR="/home/fraudapp/fraud-app-analyzer-flask"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/fraud-app_$DATE.tar.gz \
    $PROJECT_DIR/data/ \
    $PROJECT_DIR/.env

# Keep last 30 days
find $BACKUP_DIR -name "fraud-app_*.tar.gz" -mtime +30 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-fraud-app.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
```

```
0 2 * * * /usr/local/bin/backup-fraud-app.sh
```

---

## Verification

### Check Service Status

```bash
# Service running?
sudo systemctl status fraud-app

# Listening on port 5001?
sudo ss -tlnp | grep 5001

# Recent logs
sudo journalctl -u fraud-app -n 50 --no-pager
```

### Check Nginx

```bash
# Config valid?
sudo nginx -t

# Nginx running?
sudo systemctl status nginx

# Listening on 80/443?
sudo ss -tlnp | grep -E ':(80|443)'
```

### Test Locally

```bash
# Test Gunicorn directly
curl -I http://127.0.0.1:5001/

# Should return: HTTP/1.1 200 OK
```

### Test Externally

```bash
# From another machine or browser
curl -I http://yourdomain.com/
curl -I https://yourdomain.com/

# Should return: HTTP/1.1 200 OK or HTTP/2 200
```

### Test Analysis

1. Open `https://yourdomain.com` in browser
2. Register/login
3. Enter app ID: `com.whatsapp`
4. Click "Analyze"
5. Verify results display correctly
6. Try "Download PDF" and "Send Email" features

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

**Quick diagnostics**:
```bash
# Check all services
sudo systemctl status fraud-app nginx

# View error logs
sudo journalctl -u fraud-app -p err --since today
sudo tail -f /var/log/nginx/error.log

# Test connectivity
curl -v http://127.0.0.1:5001/
curl -v http://yourdomain.com/
```

---

**Last Updated**: February 2026
