#!/bin/bash
# Debug script to check if UI changes are loaded

echo "=== Checking cruise_button.py exists ==="
ls -la /data/openpilot/selfdrive/ui/onroad/cruise_button.py

echo ""
echo "=== Checking hud_renderer.py has cruise button code ==="
grep -n "cruise_button" /data/openpilot/selfdrive/ui/onroad/hud_renderer.py

echo ""
echo "=== Clearing Python cache ==="
find /data/openpilot -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /data/openpilot -name "*.pyc" -delete 2>/dev/null

echo ""
echo "=== Restarting UI ==="
pkill -f selfdrive.ui

echo "Done! UI should restart automatically."
