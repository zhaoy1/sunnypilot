# Cruise Speed Control Buttons - Solution Summary

## The Problem
We spent considerable time adding cruise speed control buttons to the Python UI code, but they never appeared on the device despite:
- Code changes being present in files (verified via SSH)
- Device being at correct commit
- Python cache being cleared multiple times
- Device being rebooted multiple times

## Root Cause Discovery
The diagnostic script revealed the critical issue:
```
=== 9. Check if UI is Using Correct Python ===
No UI process found!
```

Investigation of `system/manager/process_config.py` showed:
```python
NativeProcess("ui", "selfdrive/ui", ["./ui"], always_run, ...),  # ENABLED
PythonProcess("raylib_ui", "selfdrive.ui.ui", always_run, enabled=False, ...),  # DISABLED
```

**Sunnypilot was using a compiled C++ UI binary (`selfdrive/ui/ui`), not the Python/PyRay UI we were modifying!**

## The Solution
Changed `system/manager/process_config.py` to:
```python
NativeProcess("ui", "selfdrive/ui", ["./ui"], always_run, enabled=False, ...),  # DISABLED
PythonProcess("raylib_ui", "selfdrive.ui.ui", always_run, enabled=True, ...),   # ENABLED
```

## Implementation Details

### Files Modified:
1. **selfdrive/ui/onroad/cruise_button.py** (NEW)
   - CruiseButton widget with "+" and "-" buttons
   - Positioned at (50, 300) and (50, 570)
   - 240px font size, white color, transparent background
   - Only visible when cruise control is enabled
   - Increments/decrements `CruiseSpeedDelta` parameter

2. **selfdrive/ui/onroad/hud_renderer.py**
   - Imports CruiseButton
   - Renders buttons when `self.is_cruise_set` is True

3. **system/manager/process_config.py**
   - Disabled native C++ UI
   - Enabled Python raylib UI

### Parameter Used:
- **CruiseSpeedDelta** (defined in `common/params_keys.h`)
  - Type: Persistent parameter
  - Used to adjust cruise speed incrementally

## How to Update Device

### SSH to device:
```bash
ssh comma@192.168.1.54
```

### Run update script:
```bash
cd /data/openpilot
chmod +x update_and_test.sh
./update_and_test.sh
```

### Verify after restart:
```bash
chmod +x verify_ui.sh
./verify_ui.sh
```

### Expected output:
- Native UI: NOT running ✓
- Python raylib UI: Running ✓
- Buttons appear when cruise control is enabled

## Commit History
- `5fc5cc60` - Initial button implementation (not working - wrong UI)
- `a5441bc7` - Added diagnostic tests
- `138ddd88` - **CRITICAL FIX**: Enabled Python UI
- `d6cd250f` - Clean implementation
- `3b577ded` - Helper scripts

## Key Learnings
1. Always check which process is actually running (native vs Python)
2. Process configuration in `system/manager/process_config.py` determines what runs
3. Sunnypilot has both C++ and Python UI implementations
4. The Python UI (raylib) was disabled by default in this fork
