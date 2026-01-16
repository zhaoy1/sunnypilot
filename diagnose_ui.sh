#!/bin/bash
# Comprehensive UI diagnostic script

echo "========================================="
echo "SUNNYPILOT UI DIAGNOSTIC SCRIPT"
echo "========================================="
echo ""

echo "=== 1. Check Git Status ==="
cd /data/openpilot
git log --oneline -1
git status --short
echo ""

echo "=== 2. Verify Test Code Exists ==="
echo "Checking hud_renderer.py for test rectangles:"
grep -n "TEST: Draw a red rectangle" selfdrive/ui/onroad/hud_renderer.py
echo ""
echo "Checking augmented_road_view.py for test rectangles:"
grep -n "TEST: Draw buttons OUTSIDE" selfdrive/ui/onroad/augmented_road_view.py
echo ""

echo "=== 3. Check UI Process ==="
ps aux | grep -E "python.*ui|selfdrive.*ui" | grep -v grep
echo ""

echo "=== 4. Check Python Import Path ==="
python3 -c "import sys; print('\n'.join(sys.path))"
echo ""

echo "=== 5. Test Import of HudRenderer ==="
python3 << 'PYEOF'
try:
    from openpilot.selfdrive.ui.onroad.hud_renderer import HudRenderer
    import inspect
    source_file = inspect.getfile(HudRenderer)
    print(f"HudRenderer loaded from: {source_file}")

    # Check if the _render method has our test code
    source = inspect.getsource(HudRenderer._render)
    if "TEST: Draw a red rectangle" in source:
        print("✓ Test code IS present in loaded HudRenderer class")
    else:
        print("✗ Test code NOT found in loaded HudRenderer class")
        print("This means Python is loading from a different location!")
except Exception as e:
    print(f"Error: {e}")
PYEOF
echo ""

echo "=== 6. Check for Precompiled Files ==="
find /data/openpilot/selfdrive/ui -name "*.pyc" -o -name "*.pyo" 2>/dev/null
echo ""

echo "=== 7. Check __pycache__ Directories ==="
find /data/openpilot/selfdrive/ui -type d -name __pycache__ 2>/dev/null
echo ""

echo "=== 8. Check UI Logs ==="
echo "Last 20 lines of UI output:"
journalctl -u comma --no-pager | grep -i "ui\|error\|exception" | tail -20
echo ""

echo "=== 9. Check if UI is Using Correct Python ==="
UI_PID=$(pgrep -f "python.*ui\.py" | head -1)
if [ -n "$UI_PID" ]; then
    echo "UI Process ID: $UI_PID"
    ls -la /proc/$UI_PID/exe
    cat /proc/$UI_PID/cmdline | tr '\0' ' '
    echo ""
else
    echo "No UI process found!"
fi
echo ""

echo "========================================="
echo "DIAGNOSTIC COMPLETE"
echo "========================================="
