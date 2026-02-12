# Deployment Guide

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Environment Setup](#production-environment-setup)
3. [Deployment Methods](#deployment-methods)
4. [Security Hardening](#security-hardening)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling Strategies](#scaling-strategies)
8. [Continuous Deployment](#continuous-deployment)

---

## Pre-Deployment Checklist

### Code Preparation

- [ ] All tests pass
- [ ] Debug mode disabled (`DEBUG=False`)
- [ ] Secret key changed from default
- [ ] Strong admin password set
- [ ] Sensitive data removed from code
- [ ] `.env.example` created (no real credentials)
- [ ] `.gitignore` excludes `.env`, `*.pyc`, `__pycache__/`

### Infrastructure

- [ ] Domain name registered and DNS configured
- [ ] SSL certificate ready (or Let's Encrypt configured)
- [ ] Server meets minimum requirements (2GB RAM, Python 3.8+)
- [ ] Firewall rules defined (ports 80, 443, 22)
- [ ] Backup strategy planned
- [ ] Monitoring solution chosen

### Configuration

- [ ] Production `.env` file prepared
- [ ] SMTP credentials validated
- [ ] Gunicorn workers calculated (CPU cores)
- [ ] Nginx config tested
- [ ] Systemd service file created
- [ ] Log rotation configured

---

## Production Environment Setup

### Server Requirements

**Minimum Specs**:
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, Oracle Linux 8+)
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 10GB
- **Network**: Public IPv4, domain name

**Recommended Specs**:
- **CPU**: 4 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: Static IP, CDN (for static files)

### Cloud Providers

**AWS EC2**:
```bash
# Instance type: t3.medium (2 vCPU, 4GB RAM)
# OS: Ubuntu Server 22.04 LTS
# Security Group: Allow 22, 80, 443

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key \
    --security-group-ids sg-xxxxx
```

**DigitalOcean**:
```bash
# Droplet: Basic ($12/mo - 2 vCPU, 2GB RAM)
# OS: Ubuntu 22.04 LTS
# Datacenter: Nearest to target users

doctl compute droplet create fraud-app \
    --image ubuntu-22-04-x64 \
    --size s-2vcpu-2gb \
    --region nyc1 \
    --ssh-keys your-key-id
```

**Oracle Cloud (Free Tier)**:
```bash
# VM: VM.Standard.E2.1.Micro (1 OCPU, 1GB RAM)
# OS: Oracle Linux 8
# Free tier includes 2 instances

# Create instance via OCI Console or Terraform
```

**Hestia Control Panel**:
- Pre-configured web server management
- Automatic Nginx + PHP-FPM setup
- One-click SSL with Let's Encrypt
- Use automated installer: `Install on Hestia oracle server.sh`

### DNS Configuration

**A Records**:
```
yourdomain.com    A    203.0.113.10
www.yourdomain.com    A    203.0.113.10
```

**CNAME (alternative)**:
```
www.yourdomain.com    CNAME    yourdomain.com
```

**Verification**:
```bash
# Check DNS propagation
dig yourdomain.com +short
nslookup yourdomain.com

# Wait for propagation (up to 48 hours)
```

---

## Deployment Methods

### Method 1: Automated Installer (Recommended for Hestia)

**For Hestia/Oracle/RHEL servers**:

```bash
# 1. Clone repository
cd /home/Ian-Lusule/web/yourdomain.com/public_html
git clone https://github.com/Ian-Lusule/fraud-app-analyzer-flask.git
cd fraud-app-analyzer-flask

# 2. Edit installer configuration
nano "Install on Hestia oracle server.sh"

# Update variables:
# DOMAIN="yourdomain.com"
# PROJECT_DIR="/home/Ian-Lusule/web/yourdomain.com/public_html/fraud-app-analyzer-flask"
# USER="Ian-Lusule"
# EMAIL_FOR_CERT="admin@yourdomain.com"

# 3. Run installer
sudo bash "Install on Hestia oracle server.sh"

# 4. Verify
sudo systemctl status fraud-app
curl -I https://yourdomain.com/
```

**What the installer does**:
- Installs system dependencies
- Creates Python virtual environment
- Installs Python packages
- Creates `wsgi.py` with ReportLab patch
- Configures Gunicorn systemd service
- Sets up Nginx reverse proxy
- Obtains SSL certificate (Let's Encrypt)
- Configures firewall

### Method 2: Manual Deployment

**See detailed steps**: [INSTALLATION.md - Manual Production Setup](INSTALLATION.md#manual-production-setup)

**Summary**:
```bash
# 1. System packages
sudo apt-get update && sudo apt-get install -y \
    python3 python3-venv python3-dev nginx certbot

# 2. Clone and setup project
git clone <repo-url> fraud-app-analyzer-flask
cd fraud-app-analyzer-flask
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
nano .env  # Update SECRET_KEY, passwords, SMTP

# 4. Create wsgi.py
cat > wsgi.py <<'EOF'
import reportlab_patch
from app import create_app
app = create_app()
EOF

# 5. Systemd service
sudo nano /etc/systemd/system/fraud-app.service
# (See INSTALLATION.md for full config)

sudo systemctl enable fraud-app
sudo systemctl start fraud-app

# 6. Nginx config
sudo nano /etc/nginx/sites-available/fraud-app
# (See CONFIGURATION.md for full config)

sudo ln -s /etc/nginx/sites-available/fraud-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 7. SSL certificate
sudo certbot --nginx -d yourdomain.com

# 8. Firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Method 3: Docker Deployment

**Create Dockerfile**:
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data/results

# Expose port
EXPOSE 5001

# Run with Gunicorn
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5001", "--timeout", "120", "wsgi:app"]
```

**Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: fraud-app
    restart: always
    ports:
      - "127.0.0.1:5001:5001"
    volumes:
      - ./data:/app/data
      - ./flask_session:/app/flask_session
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    networks:
      - fraud-app-network

  nginx:
    image: nginx:alpine
    container_name: fraud-app-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static:/var/www/static:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - app
    networks:
      - fraud-app-network

networks:
  fraud-app-network:
    driver: bridge
```

**Deploy**:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f app

# Restart
docker-compose restart app

# Stop
docker-compose down
```

---

## Security Hardening

### SSH Access

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no  # Use SSH keys only

sudo systemctl restart sshd
```

### Firewall Configuration

**UFW (Ubuntu/Debian)**:
```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow services
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable
sudo ufw enable
sudo ufw status verbose
```

**Firewalld (RHEL/CentOS)**:
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

### Fail2Ban

Protect against brute-force attacks:
```bash
# Install
sudo apt-get install fail2ban

# Configure
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### Application Security

**1. Environment Variables**:
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use strong SECRET_KEY (64+ chars)
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**2. Session Security** (config.py):
```python
SESSION_COOKIE_SECURE = True       # HTTPS only
SESSION_COOKIE_HTTPONLY = True     # No JS access
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection
```

**3. Headers** (nginx):
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**4. Rate Limiting** (nginx):
```nginx
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

location /auth/login {
    limit_req zone=login_limit burst=3 nodelay;
    # ...
}
```

### Regular Updates

```bash
# System packages
sudo apt-get update && sudo apt-get upgrade -y

# Python packages
source venv/bin/activate
pip list --outdated
pip install --upgrade <package>

# Security patches
sudo unattended-upgrades  # Enable automatic security updates
```

---

## Monitoring & Logging

### Application Logs

**Gunicorn logs**:
```bash
# In systemd service
ExecStart=/path/to/gunicorn \
    --access-logfile /var/log/fraud-app/access.log \
    --error-logfile /var/log/fraud-app/error.log \
    --log-level info \
    wsgi:app

# Create log directory
sudo mkdir -p /var/log/fraud-app
sudo chown fraudapp:fraudapp /var/log/fraud-app
```

**View logs**:
```bash
# Real-time
sudo tail -f /var/log/fraud-app/error.log

# Search for errors
sudo grep -i error /var/log/fraud-app/error.log

# Journalctl
sudo journalctl -u fraud-app -f
```

### Log Rotation

**/etc/logrotate.d/fraud-app**:
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
        systemctl reload fraud-app > /dev/null 2>&1 || true
    endscript
}
```

### Nginx Logs

```bash
# Access log
sudo tail -f /var/log/nginx/access.log

# Error log
sudo tail -f /var/log/nginx/error.log

# Analyze traffic
sudo goaccess /var/log/nginx/access.log -o /var/www/html/report.html --log-format=COMBINED
```

### System Monitoring

**Install monitoring tools**:
```bash
# htop - interactive process viewer
sudo apt-get install htop

# iotop - I/O monitoring
sudo apt-get install iotop

# nethogs - network monitoring
sudo apt-get install nethogs
```

**Monitor resources**:
```bash
# CPU & memory
htop

# Disk usage
df -h
du -sh /home/fraudapp/fraud-app-analyzer-flask/data/*

# Disk I/O
sudo iotop

# Network
sudo nethogs
```

### Uptime Monitoring

**External services** (recommended):
- UptimeRobot (free plan: 50 monitors)
- Pingdom
- StatusCake
- Healthchecks.io

**Self-hosted**:
```bash
# Simple cron health check
crontab -e
```

```cron
# Check every 5 minutes
*/5 * * * * curl -fsS --retry 3 https://yourdomain.com/ > /dev/null || echo "Site down!" | mail -s "Alert" admin@yourdomain.com
```

### Application Metrics

**Track in application**:
```python
# Add to main.py
import time
from flask import g, request

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        response.headers['X-Request-Time'] = str(elapsed)
        # Log slow requests
        if elapsed > 1.0:
            app.logger.warning(f"Slow request: {request.path} took {elapsed:.2f}s")
    return response
```

---

## Backup & Recovery

### What to Backup

1. **Application data**:
   - `data/users.json`
   - `data/messages.json`
   - `data/search_logs.csv`
   - `data/results/*.json`

2. **Configuration**:
   - `.env`
   - Nginx config
   - Systemd service file

3. **SSL certificates**:
   - `/etc/letsencrypt/`

### Backup Script

**/usr/local/bin/backup-fraud-app.sh**:
```bash
#!/bin/bash
set -euo pipefail

# Configuration
BACKUP_DIR="/backups/fraud-app"
PROJECT_DIR="/home/fraudapp/fraud-app-analyzer-flask"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application data
tar -czf "$BACKUP_DIR/fraud-app-data_$DATE.tar.gz" \
    -C "$PROJECT_DIR" data/

# Backup configuration
tar -czf "$BACKUP_DIR/fraud-app-config_$DATE.tar.gz" \
    "$PROJECT_DIR/.env" \
    /etc/nginx/sites-available/fraud-app \
    /etc/systemd/system/fraud-app.service

# Backup SSL certificates
sudo tar -czf "$BACKUP_DIR/fraud-app-ssl_$DATE.tar.gz" \
    -C /etc letsencrypt/

# Remove old backups
find "$BACKUP_DIR" -name "fraud-app-*_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Log completion
echo "[$DATE] Backup completed successfully" >> "$BACKUP_DIR/backup.log"
```

```bash
sudo chmod +x /usr/local/bin/backup-fraud-app.sh
```

### Automated Backups

**Cron schedule**:
```bash
sudo crontab -e
```

```cron
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-fraud-app.sh

# Weekly backup to remote (optional)
0 3 * * 0 rsync -avz /backups/fraud-app/ user@backup-server:/backups/fraud-app/
```

### Restore Procedure

```bash
# 1. Stop application
sudo systemctl stop fraud-app

# 2. Restore data
cd /home/fraudapp/fraud-app-analyzer-flask
tar -xzf /backups/fraud-app/fraud-app-data_YYYYMMDD_HHMMSS.tar.gz

# 3. Restore config
tar -xzf /backups/fraud-app/fraud-app-config_YYYYMMDD_HHMMSS.tar.gz -C /

# 4. Restore SSL (if needed)
sudo tar -xzf /backups/fraud-app/fraud-app-ssl_YYYYMMDD_HHMMSS.tar.gz -C /etc/

# 5. Fix permissions
sudo chown -R fraudapp:fraudapp /home/fraudapp/fraud-app-analyzer-flask/data

# 6. Restart
sudo systemctl start fraud-app
sudo systemctl restart nginx
```

---

## Scaling Strategies

### Vertical Scaling (Single Server)

**Increase resources**:
```bash
# More Gunicorn workers
-w 8  # Was 3

# More memory
# Upgrade server: 4GB → 8GB RAM

# Better CPU
# Upgrade: 2 cores → 4 cores
```

### Horizontal Scaling (Multiple Servers)

**Load balancer** (Nginx):
```nginx
upstream fraud_app_backend {
    least_conn;
    server 10.0.1.10:5001 weight=1;
    server 10.0.1.11:5001 weight=1;
    server 10.0.1.12:5001 weight=1;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://fraud_app_backend;
        # ... proxy headers
    }
}
```

**Shared storage** (required for multi-server):
```bash
# Option 1: NFS
# Option 2: S3/MinIO
# Option 3: Database (migrate from JSON to PostgreSQL)
```

### Caching

**Redis session storage**:
```python
# config.py
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url('redis://localhost:6379')
```

**Nginx caching**:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m inactive=60m;

location /static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## Continuous Deployment

### Git Hooks

**Post-receive hook** (on server):
```bash
#!/bin/bash
# /home/fraudapp/fraud-app.git/hooks/post-receive

GIT_DIR="/home/fraudapp/fraud-app.git"
WORK_TREE="/home/fraudapp/fraud-app-analyzer-flask"

git --work-tree="$WORK_TREE" --git-dir="$GIT_DIR" checkout -f

cd "$WORK_TREE"
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fraud-app

echo "Deployment completed: $(date)"
```

**Deploy from local**:
```bash
# Add remote
git remote add production fraudapp@yourdomain.com:fraud-app.git

# Deploy
git push production main
```

### CI/CD with GitHub Actions

**.github/workflows/deploy.yml**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /home/fraudapp/fraud-app-analyzer-flask
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart fraud-app
```

---

**Last Updated**: February 2026
