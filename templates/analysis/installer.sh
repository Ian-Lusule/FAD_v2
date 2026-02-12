#!/bin/bash
set -e

# Variables
APP_DIR="/home/ianlus/web/fad.lusule.com/public_html/fraud-app-analyzer-flask"
SERVICE_NAME="fadlusule"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
NGINX_CONF="/etc/nginx/sites-available/fad.lusule.com"
USER="ianlus"
GROUP="ianlus"

echo "=== Setting up fad.lusule.com ==="

read -p "Enter full scanner command: " SCANNER_CMD
[ -z "$SCANNER_CMD" ] && { echo "Scanner command required."; exit 1; }

sudo apt-get update
sudo apt-get install -y python3 python3-pip nginx proxychains

sudo mkdir -p "$APP_DIR/logs"
sudo chown -R "$USER:$GROUP" "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

echo "Installing Flask + dependencies system-wide..."
sudo pip3 install --upgrade pip
sudo pip3 install -r "$APP_DIR/requirements.txt" || sudo pip3 install flask

# systemd service – use gunicorn if in requirements.txt, else flask dev (not ideal)
cat <<EOF | sudo tee "$SERVICE_FILE" >/dev/null
[Unit]
Description=Flask Fraud App Analyzer (fad)
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
ExecStart=/usr/bin/python3 -m flask run --host=127.0.0.1 --port=5001
Restart=on-failure
RestartSec=5s
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

systemctl is-active --quiet "$SERVICE_NAME" || {
    echo "Service failed."; sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager; exit 1;
}

# cron (adjust endpoint if needed – assuming /urls exists)
CRON_LOG="/var/log/fadlusule-cron.log"
sudo touch "$CRON_LOG"
sudo chown "$USER:$GROUP" "$CRON_LOG"
sudo chmod 644 "$CRON_LOG"

(crontab -u "$USER" -l 2>/dev/null; echo "*/30 * * * * proxychains curl -s http://fad.lusule.com/urls | $SCANNER_CMD >> $CRON_LOG 2>&1") | crontab -u "$USER" -

# nginx
cat <<EOF | sudo tee "$NGINX_CONF" >/dev/null
server {
    listen 80;
    server_name fad.lusule.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

[ -L /etc/nginx/sites-enabled/fad.lusule.com ] && sudo rm /etc/nginx/sites-enabled/fad.lusule.com
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/

sudo nginx -t || { echo "Nginx config failed."; exit 1; }
sudo systemctl restart nginx

systemctl is-active --quiet nginx || { echo "Nginx failed."; sudo journalctl -u nginx -n 50 --no-pager; exit 1; }

echo "Done."
echo "status:  sudo systemctl status $SERVICE_NAME"
echo "logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "cron log: $CRON_LOG"