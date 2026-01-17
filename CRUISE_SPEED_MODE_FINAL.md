# Cruise Speed Mode - Final Implementation

## Overview
Feature that allows users to set cruise speed based on speed limits instead of current vehicle speed.

**4 Modes Available:**
- Mode 0: Current Speed (default/original behavior)
- Mode 1: Speed Limit (exact)
- Mode 2: Speed Limit + 10%
- Mode 3: Speed Limit + 20%

## Storage Solution
**File-based storage** (not Params system):
- **Location**: `/data/params/d/CruiseSpeedMode`
- **Format**: Plain text file containing integer 0-3
- **Default**: 0
- **Why**: Avoids requiring recompilation of `params_pyx.so` binary

## Files Modified

### 1. `selfdrive/car/cruise.py`
Core cruise control logic.

**New methods:**
- `read_cruise_speed_mode()`: Reads mode from file
- `calculate_cruise_speed_from_limit()`: Calculates cruise speed based on mode
- `update_speed_limit()`: Updates speed limit from roadLimitSpeed (m/s → kph)

**Modified:**
- `initialize_v_cruise()`: Re-reads mode on every engagement, uses speed limit when mode > 0

### 2. `selfdrive/car/card.py`
Speed limit data subscription.

**Changes:**
- Added `'roadLimitSpeed'` to SubMaster
- Validates: `speedLimitValid == True` AND `speedLimit > 0`
- Calls `update_speed_limit()` with validated data

### 3. `selfdrive/ui/sunnypilot/layouts/settings/cruise.py`
UI settings control.

**New:**
- `CruiseSpeedModeButton` widget with mode selection dialog
- Reads/writes mode from/to file
- Displays: "Cruise Speed Mode: [mode name]"

## Usage
1. Settings → Cruise → "Cruise Speed Mode"
2. Select mode
3. Engage cruise - speed set according to mode
4. Changes take effect immediately (no restart)

## Status
✅ Device boots successfully
✅ No errors in logs
✅ File-based storage working
⏳ Needs testing: UI interaction and cruise engagement with different modes
