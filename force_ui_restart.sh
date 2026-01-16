#!/bin/bash
# Aggressive UI restart script

echo "=== Step 1: Kill all UI processes ==="
pkill -9 -f "selfdrive.ui"
pkill -9 -f "ui.py"
pkill -9 -f "python.*ui"
sleep 2

echo ""
echo "=== Step 2: Clear ALL Python cache ==="
find /data/openpilot -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /data/openpilot -name "*.pyc" -delete 2>/dev/null
find /data/openpilot -name "*.pyo" -delete 2>/dev/null
find /data -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /data -name "*.pyc" -delete 2>/dev/null

echo ""
echo "=== Step 3: Verify code changes are present ==="
echo "Checking for test rectangles in hud_renderer.py:"
grep -n "TEST: Draw a red rectangle" /data/openpilot/selfdrive/ui/onroad/hud_renderer.py

echo ""
echo "Checking for test rectangles in augmented_road_view.py:"
grep -n "TEST: Draw buttons OUTSIDE" /data/openpilot/selfdrive/ui/onroad/augmented_road_view.py

echo ""
echo "=== Step 4: Check if UI process is running ==="
ps aux | grep -E "ui\.py|selfdrive.*ui" | grep -v grep

echo ""
echo "=== Step 5: Restart manager (will restart all processes) ==="
sudo systemctl restart comma
# OR if that doesn't work:
# sudo reboot

echo ""
echo "Done! Wait 30 seconds for system to fully restart."
echo "If still not working, the issue may be:"
echo "1. UI is running from a different code location"
echo "2. There's a precompiled binary being used"
echo "3. The UI process is managed differently in sunnypilot"
