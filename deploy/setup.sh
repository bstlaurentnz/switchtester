#!/bin/bash
set -e

cd "$(dirname "$0")/.."
INSTALL_DIR=$(pwd)
SERVICE_USER=$(whoami)

# Install Python deps
uv sync

# Hotspot -- skip if profile already exists
sudo nmcli con add type wifi ifname wlan0 mode ap \
  con-name SwitchTester ssid SwitchTester 2>/dev/null || true
sudo nmcli con modify SwitchTester \
  ipv4.method shared \
  ipv4.addresses 10.42.0.1/24 \
  802-11-wireless.band bg \
  802-11-wireless.channel 6 \
  connection.autoconnect yes
sudo nmcli con up SwitchTester

# Write systemd service with resolved paths
sudo tee /etc/systemd/system/switchtester-web.service > /dev/null <<EOF
[Unit]
Description=Switch Tester Web UI
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/switch-tester-web
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable switchtester-web
sudo systemctl start switchtester-web

echo "Done. Connect to WiFi: SwitchTester  ->  http://10.42.0.1:5000"
