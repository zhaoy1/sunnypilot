#!/bin/bash
# Script to update device and verify Python UI is running

echo "========================================="
echo "SUNNYPILOT UPDATE & TEST SCRIPT"
echo "========================================="
echo ""

echo "=== Step 1: Update code on device ==="
cd /data/openpilot
git fetch origin
git checkout based-on-release-tizi
git reset --hard origin/based-on-release-tizi
echo "Current commit: $(git log --oneline -1)"
echo ""

echo "=== Step 2: Clear Python cache ==="
find /data/openpilot -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find /data/openpilot -name "*.pyc" -delete 2>/dev/null
echo "Cache cleared"
echo ""

echo "=== Step 3: Verify process_config changes ==="
echo "Checking if Python UI is enabled:"
grep -A1 "raylib_ui" /data/openpilot/system/manager/process_config.py | grep "enabled"
echo ""

echo "=== Step 4: Restart manager (this will restart all processes) ==="
echo "Restarting in 3 seconds..."
sleep 3
sudo systemctl restart comma

echo ""
echo "========================================="
echo "UPDATE COMPLETE"
echo "========================================="
echo ""
echo "Wait 30 seconds for system to fully restart, then:"
echo "1. Go to onroad view (start driving or engage cruise)"
echo "2. You should see '+' and '-' buttons when cruise is enabled"
echo ""
echo "To check if Python UI is running:"
echo "  ps aux | grep raylib_ui"
echo ""
