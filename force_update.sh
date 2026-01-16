#!/bin/bash
# Force update script - run this on the device via SSH

echo "=== Current commit ==="
cd /data/openpilot
git rev-parse HEAD
git log --oneline -1

echo ""
echo "=== Checking if our code is in the file ==="
grep -n "Draw + and - buttons next to the speed" /data/openpilot/selfdrive/ui/onroad/hud_renderer.py

echo ""
echo "=== Removing ALL Python cache ==="
find /data/openpilot -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /data/openpilot -name "*.pyc" -delete 2>/dev/null
find /data/openpilot -name "*.pyo" -delete 2>/dev/null

echo ""
echo "=== Killing all Python processes ==="
pkill -9 python3

echo ""
echo "=== Rebooting system ==="
reboot
