#!/bin/bash

# Stop the access point
sudo nmcli con down SwitchTester

# Remove the dnsmasq captive portal config
sudo rm -f /etc/dnsmasq.d/captive-portal.conf
sudo systemctl restart dnsmasq

# Flush the iptables NAT rules you added
sudo iptables -t nat -S PREROUTING | grep "switchtester" | while read -r rule; do
  sudo iptables -t nat $(echo "$rule" | sed 's/^-A/-D/')
done

# If you used the old flush approach and want a clean slate
# sudo iptables -t nat -F PREROUTING

# Save the cleaned-up rules
sudo netfilter-persistent save
