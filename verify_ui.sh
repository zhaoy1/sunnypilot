#!/bin/bash
# Quick verification script

echo "=== Checking UI Process ==="
echo ""
echo "Native UI (should NOT be running):"
ps aux | grep "selfdrive/ui" | grep "./ui" | grep -v grep || echo "  ✓ Not running (good!)"
echo ""
echo "Python raylib UI (should be running):"
ps aux | grep "raylib_ui" | grep -v grep || echo "  ✗ Not running (bad!)"
echo ""

echo "=== Checking Process Config ==="
echo "Native UI enabled status:"
grep -A1 'NativeProcess("ui"' /data/openpilot/system/manager/process_config.py | grep enabled
echo ""
echo "Python UI enabled status:"
grep -A1 'PythonProcess("raylib_ui"' /data/openpilot/system/manager/process_config.py | grep enabled
echo ""

echo "=== Checking Code Changes ==="
echo "Cruise button file exists:"
ls -la /data/openpilot/selfdrive/ui/onroad/cruise_button.py
echo ""
echo "HUD renderer has cruise button import:"
grep "cruise_button" /data/openpilot/selfdrive/ui/onroad/hud_renderer.py | head -2
echo ""
