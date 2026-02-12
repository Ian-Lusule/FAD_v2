# Troubleshooting Guide

## Table of Contents

1. [Common Installation Issues](#common-installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Service Issues](#service-issues)
4. [Nginx Issues](#nginx-issues)
5. [SSL Certificate Issues](#ssl-certificate-issues)
6. [Email Issues](#email-issues)
7. [Analysis & PDF Issues](#analysis--pdf-issues)
8. [Performance Issues](#performance-issues)
9. [Debugging Tools](#debugging-tools)

---

## Common Installation Issues

### Python Version Mismatch

**Symptom**:
```
python3: command not found
-or-
Python 3.8 or higher is required
```

**Solution**:
```bash
# Check Python version
python3 --version

# Install Python 3.8+ (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3.9-dev

# Use specific version
python3.9 -m venv venv
```

### Pip Installation Failures

**Symptom**:
```
error: externally-managed-environment
```

**Solution**:
Always use virtual environment:
```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Now install packages
pip install -r requirements.txt
```

### Build Dependencies Missing

**Symptom**:
```
error: command 'gcc' failed
-or-
python.h: No such file or directory
```

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# RHEL/CentOS/Oracle
sudo dnf install gcc gcc-c++ python3-devel
```

### Permission Denied

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**Solution**:
```bash
# Fix ownership
sudo chown -R Ian-Lusule:Ian-Lusule /path/to/fraud-app-analyzer-flask

# Fix permissions
chmod 755 /path/to/fraud-app-analyzer-flask
chmod 644 /path/to/fraud-app-analyzer-flask/data/*.json
```

---

## Runtime Errors

### AttributeError: 'str' object has no attribute 'get'

**Symptom**:
```python
AttributeError: 'str' object has no attribute 'get'
File "templates/analysis/results.html", line X
{{ classification_metrics.get('accuracy', 'N/A') }}
```

**Root Cause**: 
`classification_metrics` is sometimes a string instead of dict.

**Solution** (already implemented):
[modules/report_generator.py](../modules/report_generator.py#L200-L210) normalizes payload:
```python
def _ensure_dict(value, key_name="value"):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return {}
    elif isinstance(value, SimpleNamespace):
        return value.__dict__
    return value if isinstance(value, dict) else {}
```

**Verification**:
```bash
# Check if patch is applied
grep -n "_ensure_dict" modules/report_generator.py
```

### Jinja2 UndefinedError

**Symptom**:
```
jinja2.exceptions.UndefinedError: 'None' has no attribute 'get'
```

**Solution**:
Templates use defensive checks:
```jinja2
{# Safe access #}
{{ metrics.get('accuracy', 'N/A') if metrics else 'N/A' }}

{# Or use default filter #}
{{ (metrics.accuracy | default('N/A')) if metrics else 'N/A' }}
```

**Verify in templates**:
```bash
# Check templates for unsafe access
grep -r "\.get(" templates/
```

### ImportError: No module named 'flask'

**Symptom**:
```
ImportError: No module named 'flask'
ModuleNotFoundError: No module named 'flask'
```

**Solution**:
```bash
# Activate venv first!
source venv/bin/activate

# Verify venv is active (should show venv path)
which python
# Output: /path/to/fraud-app-analyzer-flask/venv/bin/python

# Reinstall requirements
pip install -r requirements.txt
```

---

## Service Issues

### Service Won't Start

**Symptom**:
```bash
sudo systemctl status fraud-app
● fraud-app.service - Gunicorn instance serving Fraud App Analyzer
   Loaded: loaded
   Active: failed (Result: exit-code)
```

**Diagnosis**:
```bash
# Check detailed logs
sudo journalctl -u fraud-app -n 50 --no-pager

# Common errors and solutions below
```

**Error: "Address already in use"**:
```
OSError: [Errno 98] Address already in use
```

Solution:
```bash
# Find process using port 5001
sudo lsof -i :5001

# Kill the process
sudo kill -9 <PID>

# Or change port in systemd service
sudo nano /etc/systemd/system/fraud-app.service
# Change: -b 127.0.0.1:5002

sudo systemctl daemon-reload
sudo systemctl restart fraud-app
```

**Error: "Permission denied"**:
```
PermissionError: [Errno 13] Permission denied
```

Solution:
```bash
# Fix ownership
sudo chown -R fraudapp:fraudapp /home/fraudapp/fraud-app-analyzer-flask

# Fix data directory permissions
sudo chmod 755 /home/fraudapp/fraud-app-analyzer-flask/data
sudo chmod 644 /home/fraudapp/fraud-app-analyzer-flask/data/*.json
```

**Error: "No such file or directory: wsgi:app"**:
```
Error: 'wsgi:app' doesn't exist
```

Solution:
```bash
# Ensure wsgi.py exists
cd /path/to/fraud-app-analyzer-flask
cat > wsgi.py <<'EOF'
import reportlab_patch
from app import create_app

app = create_app()
EOF

# Verify WorkingDirectory in service file
sudo nano /etc/systemd/system/fraud-app.service
# Should point to project root
```

### Service Keeps Restarting

**Symptom**:
```bash
sudo systemctl status fraud-app
Active: activating (auto-restart)
```

**Diagnosis**:
```bash
# Watch logs in real-time
sudo journalctl -u fraud-app -f

# Check for repeated errors
sudo journalctl -u fraud-app --since "5 minutes ago"
```

**Common causes**:
1. Missing `.env` file
2. Invalid Python syntax
3. Missing dependencies
4. Database/file access issues

**Solution**:
```bash
# Test manually
cd /path/to/fraud-app-analyzer-flask
source venv/bin/activate
python wsgi.py
# Check for errors

# If successful, restart service
sudo systemctl restart fraud-app
```

---

## Nginx Issues

### 502 Bad Gateway

**Symptom**:
Browser shows: "502 Bad Gateway"

**Diagnosis**:
```bash
# Check if Gunicorn is running
sudo systemctl status fraud-app

# Check if port 5001 is listening
sudo ss -tlnp | grep 5001

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

**Solution**:
```bash
# If Gunicorn not running
sudo systemctl start fraud-app

# If port mismatch in Nginx config
sudo nano /etc/nginx/sites-available/fraud-app
# Ensure: proxy_pass http://127.0.0.1:5001;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 403 Forbidden / Access Denied

**Symptom**:
```
403 Forbidden
nginx/1.x.x
```

**Root Cause** (Hestia-specific):
Default Hestia server block takes precedence over custom config.

**Solution**:
Add explicit IP binding to server block:
```nginx
server {
    # Get public IP first
    # ip addr show | grep "inet.*global"
    
    listen 10.0.0.205:80;  # Replace with your public IP
    listen [::]:80;
    server_name yourdomain.com;
    # ... rest of config
}
```

**Apply changes**:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 404 Not Found for Static Files

**Symptom**:
Static files (CSS/JS) return 404

**Solution**:
```nginx
# Add to server block
location /static/ {
    alias /full/path/to/fraud-app-analyzer-flask/static/;
    expires 30d;
}

# Ensure trailing slashes match!
# Both must have / at end: /static/ and /path/static/
```

**Verify permissions**:
```bash
# Nginx user needs read access
sudo chmod 755 /path/to/fraud-app-analyzer-flask
sudo chmod 755 /path/to/fraud-app-analyzer-flask/static
sudo chmod 644 /path/to/fraud-app-analyzer-flask/static/css/*.css
```

### Nginx Won't Start

**Symptom**:
```bash
sudo systemctl status nginx
Active: failed
```

**Diagnosis**:
```bash
# Test configuration
sudo nginx -t
```

**Common errors**:

**"duplicate listen options"**:
```
nginx: [emerg] duplicate listen options for 0.0.0.0:80
```

Solution: Remove duplicate `listen` directives in config.

**"could not build server_names_hash"**:
```
nginx: [emerg] could not build server_names_hash
```

Solution:
```nginx
# Add to http block in /etc/nginx/nginx.conf
http {
    server_names_hash_bucket_size 64;
    # ...
}
```

---

## SSL Certificate Issues

### Certbot Challenge Fails

**Symptom**:
```
Certbot failed to authenticate some domains
Challenge failed for domain yourdomain.com
```

**Diagnosis**:
```bash
# Test .well-known access
curl http://yourdomain.com/.well-known/acme-challenge/test
```

**Solution 1**: Ensure nginx serves `.well-known`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
```

**Solution 2**: Use webroot authenticator:
```bash
sudo certbot certonly \
    --webroot \
    -w /var/www/html \
    -d yourdomain.com \
    -d www.yourdomain.com
```

**Solution 3**: Check firewall:
```bash
# Ensure port 80 is open
sudo ufw status
sudo ufw allow 80/tcp
```

### Certificate Expired

**Symptom**:
```
NET::ERR_CERT_DATE_INVALID
Your connection is not private
```

**Solution**:
```bash
# Check certificate expiry
sudo certbot certificates

# Renew manually
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run

# Check certbot timer
sudo systemctl status certbot.timer
sudo systemctl enable certbot.timer
```

### Mixed Content Warnings

**Symptom**:
Browser console: "Mixed Content: The page was loaded over HTTPS, but..."

**Solution**:
Ensure all assets use HTTPS or protocol-relative URLs:
```html
<!-- Bad -->
<script src="http://example.com/script.js"></script>

<!-- Good -->
<script src="https://example.com/script.js"></script>
<script src="//example.com/script.js"></script>
```

Add to nginx:
```nginx
add_header Content-Security-Policy "upgrade-insecure-requests";
```

---

## Email Issues

### SMTP Authentication Failed

**Symptom**:
```
SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```

**Solution for Gmail**:
1. Enable 2FA: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use app password in `.env`:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password  # Not your regular password!
```

### SMTP Connection Timeout

**Symptom**:
```
smtplib.SMTPConnectError: (10060, 'Connection timed out')
```

**Solution**:
```bash
# Check firewall allows outbound SMTP
sudo ufw status

# Allow outbound on 587 (may need to configure firewall)
# Some providers block port 25

# Test connectivity
telnet smtp.gmail.com 587
# Should connect successfully
```

### TLS/SSL Errors

**Symptom**:
```
SMTPServerDisconnected: Connection unexpectedly closed
-or-
ssl.SSLError: [SSL: WRONG_VERSION_NUMBER]
```

**Solution**:
Verify port and TLS settings match:
```bash
# Port 587 = STARTTLS
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# Port 465 = SSL/TLS
MAIL_PORT=465
MAIL_USE_TLS=False
MAIL_USE_SSL=True
```

**Test email** (see [CONFIGURATION.md](CONFIGURATION.md#testing-email)):
```bash
python3 -c "
from dotenv import load_dotenv
import os
from flask import Flask
from flask_mail import Mail, Message

load_dotenv()
app = Flask(__name__)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)
with app.app_context():
    msg = Message('Test', recipients=['test@example.com'], body='Test email')
    mail.send(msg)
    print('Success!')
"
```

---

## Analysis & PDF Issues

### ReportLab MD5 Error (CRITICAL)

**Symptom**:
```
TypeError: 'usedforsecurity' is an invalid keyword argument for openssl_md5()
```

**Root Cause**:
Python 3.8 + OpenSSL 3.x incompatibility with ReportLab < 4.0

**Solution** (already implemented):
[reportlab_patch.py](../reportlab_patch.py) monkey-patches hashlib:
```python
import hashlib

_original_md5 = hashlib.md5

def patched_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _original_md5(*args, **kwargs)

hashlib.md5 = patched_md5
```

**Verification**:
```bash
# Ensure patch is imported BEFORE app
head -5 wsgi.py
# Should show: import reportlab_patch

# Test PDF generation
# Login → Analyze app → Click "Download PDF"
```

**Alternative solution** (upgrade ReportLab):
```bash
pip install --upgrade 'reportlab>=4.0.0'
# ReportLab 4.x has native OpenSSL 3 support
```

### Worker Timeout During PDF Generation

**Symptom**:
```
[CRITICAL] WORKER TIMEOUT (pid:12345)
```

**Root Cause**:
WordCloud generation is CPU-intensive.

**Solution**:
Increase Gunicorn timeout:
```bash
# Edit systemd service
sudo nano /etc/systemd/system/fraud-app.service

# Change timeout
ExecStart=/path/to/gunicorn \
    --timeout 180 \  # Increase from 120 to 180
    wsgi:app

sudo systemctl daemon-reload
sudo systemctl restart fraud-app
```

### "No reviews found" Error

**Symptom**:
Analysis completes but shows "No reviews found"

**Diagnosis**:
```python
# Check if app exists on Play Store
from google_play_scraper import app

result = app('com.whatsapp')
print(result)  # Should return app details
```

**Possible causes**:
1. Invalid app ID
2. App not available in your region
3. Play Store API rate limiting
4. App removed from store

**Solution**:
```python
# Test with known apps
# Valid: com.whatsapp, com.facebook.katana, com.instagram.android
# Try different country
from google_play_scraper import reviews

result, _ = reviews(
    'com.whatsapp',
    lang='en',
    country='us',  # Try 'us', 'gb', 'in'
    count=100
)
```

### Sentiment Analysis Errors

**Symptom**:
```
LookupError: Resource punkt not found
-or-
LookupError: Resource vader_lexicon not found
```

**Solution**:
```bash
# Activate venv
source venv/bin/activate

# Download NLTK data (if using)
python3 -c "
import nltk
nltk.download('punkt')
nltk.download('vader_lexicon')
nltk.download('stopwords')
"

# For TextBlob
python3 -m textblob.download_corpora
```

---

## Performance Issues

### Slow Analysis

**Symptom**:
Analysis takes > 2 minutes

**Optimization**:
```python
# Reduce review count in main.py
reviews, _ = reviews(
    app_id,
    count=200,  # Reduce from 500 to 200
    # ...
)
```

### High Memory Usage

**Diagnosis**:
```bash
# Check memory usage
ps aux | grep gunicorn
# Note RSS column (memory in KB)

# Monitor in real-time
top -p $(pgrep -d',' -f gunicorn)
```

**Solution**:
```bash
# Reduce workers
sudo nano /etc/systemd/system/fraud-app.service
# Change: -w 2  # Reduce from 3 to 2

# Add max-requests (restart workers periodically)
ExecStart=/path/to/gunicorn \
    -w 2 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    wsgi:app

sudo systemctl daemon-reload
sudo systemctl restart fraud-app
```

### Database File Locked

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: 'data/users.json'
```

**Solution**:
```bash
# Check file ownership
ls -la data/

# Fix ownership
sudo chown fraudapp:fraudapp data/*.json

# Fix permissions
chmod 644 data/*.json
```

---

## Debugging Tools

### Enable Flask Debug Mode

**Development only**:
```bash
# .env
DEBUG=True
FLASK_ENV=development

# run.py
python run.py
# Access at http://localhost:5000
```

### View Application Logs

```bash
# Systemd service logs
sudo journalctl -u fraud-app -f

# Last 100 lines
sudo journalctl -u fraud-app -n 100 --no-pager

# Errors only
sudo journalctl -u fraud-app -p err

# Since specific time
sudo journalctl -u fraud-app --since "2024-01-01 10:00"
```

### Nginx Access Logs

```bash
# Real-time monitoring
sudo tail -f /var/log/nginx/access.log

# Find slow requests (>1s)
awk '$NF > 1.0' /var/log/nginx/access.log

# Top IPs
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

### Test Endpoints

```bash
# Health check
curl -I http://localhost:5001/

# Test with authentication
curl -b cookies.txt http://localhost:5001/dashboard

# JSON response
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Python Interactive Debugging

```python
# Add to code
import pdb; pdb.set_trace()

# Or use ipdb (better)
import ipdb; ipdb.set_trace()

# Run and interact
python run.py
# When breakpoint hits, you can inspect variables
```

### Check Service Dependencies

```bash
# Check all services
sudo systemctl status fraud-app nginx

# Check listening ports
sudo ss -tlnp | grep -E ':(80|443|5001)'

# Check connectivity
curl -v http://127.0.0.1:5001/
curl -v http://yourdomain.com/
```

---

## Getting Help

If issues persist:

1. **Collect diagnostic info**:
```bash
# System info
uname -a
python3 --version
pip list | grep -i flask

# Service status
sudo systemctl status fraud-app nginx
sudo journalctl -u fraud-app -n 50 --no-pager

# Network
sudo ss -tlnp | grep -E ':(80|443|5001)'
curl -I http://localhost:5001/
```

2. **Check existing issues**: See [GitHub Issues](#) (if applicable)

3. **Contact administrator**: Use "Contact Admin" feature in app

4. **Review logs**: All logs in `/var/log/` and `sudo journalctl`

---

**Last Updated**: February 2026
