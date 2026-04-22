#!/bin/bash
set -e

# ---------- Install apt packages if missing ----------
NEEDED=()
dpkg -s iptables-persistent &>/dev/null || NEEDED+=(iptables-persistent)
dpkg -s dnsmasq &>/dev/null || NEEDED+=(dnsmasq)

if [ ${#NEEDED[@]} -gt 0 ]; then
  echo "Installing missing packages: ${NEEDED[*]}"
  sudo apt-get install -y "${NEEDED[@]}"
else
  echo "All apt packages already installed."
fi

cd "$(dirname "$0")/.."
INSTALL_DIR=$(pwd)
SERVICE_USER=$(whoami)

# Install Python deps
uv sync

# ---------- Prevent NetworkManager from overwriting resolv.conf ----------
sudo tee /etc/NetworkManager/conf.d/dns-no-dnsmasq.conf > /dev/null <<EOF
[main]
dns=none
EOF

sudo tee /etc/resolv.conf > /dev/null <<EOF
nameserver 192.168.1.1
EOF

sudo systemctl restart NetworkManager
sleep 3

# ---------- Wired interface -- pin DNS to the router ----------
WIRED_CON=$(nmcli -t -f NAME,DEVICE con show --active | grep eth0 | cut -d: -f1)
if [ -n "$WIRED_CON" ]; then
  echo "Pinning DNS on wired connection: $WIRED_CON"
  sudo nmcli con modify "$WIRED_CON" ipv4.dns "192.168.1.1"
  sudo nmcli con modify "$WIRED_CON" ipv4.dns-priority -10
else
  echo "WARNING: No active wired connection found on eth0"
fi

# ---------- Free wlan0 for AP use ----------
# Disconnect any existing wifi client connection
ACTIVE_WIFI=$(nmcli -t -f NAME,DEVICE con show --active | grep wlan0 | cut -d: -f1)
if [ -n "$ACTIVE_WIFI" ] && [ "$ACTIVE_WIFI" != "SwitchTester" ]; then
  echo "Disconnecting $ACTIVE_WIFI to free wlan0 for AP..."
  sudo nmcli con down "$ACTIVE_WIFI"
  sudo nmcli con modify "$ACTIVE_WIFI" connection.autoconnect no
fi

# ---------- Hotspot -- only create if it doesn't exist ----------
if nmcli con show SwitchTester &>/dev/null; then
  echo "SwitchTester connection profile already exists, skipping creation."
else
  echo "Creating SwitchTester access point..."
  sudo nmcli con add type wifi ifname wlan0 mode ap \
    con-name SwitchTester ssid SwitchTester
  sudo nmcli con modify SwitchTester \
    ipv4.method shared \
    ipv4.addresses 10.42.0.1/24 \
    802-11-wireless.band bg \
    802-11-wireless.channel 6 \
    connection.autoconnect yes
fi

sudo nmcli con up SwitchTester

# ---------- Captive portal DNS (wlan0 only) ----------
sudo tee /etc/dnsmasq.d/captive-portal.conf > /dev/null <<EOF
# Only listen on the AP interface, not on eth0 or loopback
interface=wlan0
bind-interfaces
except-interface=eth0
except-interface=lo
no-dhcp-interface=eth0

# Resolve ALL domains to the Pi (only affects wlan0 clients)
address=/#/10.42.0.1

# Don't read system resolv.conf
no-resolv
no-hosts

# DHCP for AP clients only
dhcp-range=10.42.0.10,10.42.0.250,255.255.255.0,12h
EOF

sudo tee /etc/default/dnsmasq > /dev/null <<EOF
DNSMASQ_OPTS="--listen-address=10.42.0.1"
EOF

sudo systemctl enable dnsmasq
sudo systemctl restart dnsmasq

# ---------- Redirect HTTP/HTTPS to Flask on port 5000 ----------
# Remove any existing switchtester rules first (idempotent)
sudo iptables -t nat -S PREROUTING | grep "switchtester" | while read -r rule; do
  sudo iptables -t nat $(echo "$rule" | sed 's/^-A/-D/')
done

sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 \
  -m comment --comment "switchtester" \
  -j DNAT --to-destination 10.42.0.1:5000
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 \
  -m comment --comment "switchtester" \
  -j DNAT --to-destination 10.42.0.1:5000

# Persist iptables rules across reboots
sudo netfilter-persistent save

# ---------- Systemd service ----------
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