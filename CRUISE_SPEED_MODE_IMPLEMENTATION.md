# Cruise Speed Mode Implementation

## Overview
This implementation adds a cruise speed mode feature that allows the cruise control to automatically set speed based on the detected speed limit instead of just using the current vehicle speed.

## Features Implemented

### 1. New Parameter: `CruiseSpeedMode`
- **Location**: `common/params_keys.h`
- **Type**: Integer (PERSISTENT | BACKUP)
- **Values**:
  - `0` = Current Speed (default behavior)
  - `1` = Speed Limit
  - `2` = Speed Limit + 10%
  - `3` = Speed Limit + 20%

### 2. Cruise Helper Updates (`selfdrive/car/cruise.py`)

#### New Methods:
- `read_cruise_speed_mode()`: Reads the cruise speed mode from parameters
- `calculate_cruise_speed_from_limit(speed_limit_kph)`: Calculates target cruise speed based on speed limit and selected mode
- `update_speed_limit(speed_limit_ms)`: Updates the current speed limit from roadLimitSpeed

#### Modified Methods:
- `__init__()`: Added initialization of cruise speed mode and speed limit tracking
- `initialize_v_cruise()`: Modified to use speed limit based cruise when mode > 0

### 3. Card Updates (`selfdrive/car/card.py`)

#### Changes:
- Added `'roadLimitSpeed'` to SubMaster subscription
- Added speed limit update call before `update_v_cruise()`:
  ```python
  if self.sm.valid['roadLimitSpeed'] and self.sm['roadLimitSpeed'].speedLimitValid:
      self.v_cruise_helper.update_speed_limit(self.sm['roadLimitSpeed'].speedLimit)
  ```

### 4. UI Settings (`selfdrive/ui/sunnypilot/layouts/settings/cruise.py`)

#### New Components:
- `CruiseSpeedModeButton`: A button widget that opens a selection dialog
- Uses `MultiOptionDialog` for mode selection
- Displays current mode: "Cruise Speed Mode: [Current Speed/Speed Limit/Speed Limit + 10%/Speed Limit + 20%]"

## How It Works

### Flow:
1. **Speed Limit Detection**: The system receives speed limit data from `roadLimitSpeed` message (from map data or camera detection)

2. **Mode Selection**: User selects desired cruise speed mode in Settings > Cruise menu

3. **Cruise Initialization**: When cruise is enabled:
   - If mode = 0 (Current Speed): Uses current vehicle speed (default behavior)
   - If mode > 0: Calculates target speed from speed limit:
     - Mode 1: Uses exact speed limit
     - Mode 2: Uses speed limit × 1.10
     - Mode 3: Uses speed limit × 1.20

4. **Display**: The calculated cruise speed is shown in the "MAX" box on the HUD

### Example Scenarios:

**Scenario 1: Speed Limit Mode**
- Speed limit: 65 mph
- Mode: Speed Limit (1)
- Result: Cruise sets to 65 mph when enabled

**Scenario 2: Speed Limit + 10%**
- Speed limit: 100 km/h
- Mode: Speed Limit + 10% (2)
- Result: Cruise sets to 110 km/h when enabled

**Scenario 3: Current Speed (Default)**
- Current speed: 75 mph
- Mode: Current Speed (0)
- Result: Cruise sets to 75 mph when enabled (original behavior)

## Files Modified

1. `common/params_keys.h` - Added CruiseSpeedMode parameter
2. `selfdrive/car/cruise.py` - Added speed limit based cruise logic
3. `selfdrive/car/card.py` - Added roadLimitSpeed subscription and updates
4. `selfdrive/ui/sunnypilot/layouts/settings/cruise.py` - Added UI settings control

## Testing

### To Test:
1. Navigate to Settings > Cruise
2. Select "Cruise Speed Mode" button
3. Choose desired mode (Current Speed, Speed Limit, Speed Limit + 10%, or Speed Limit + 20%)
4. Drive on a road with detected speed limit
5. Enable cruise control
6. Verify the MAX speed shown matches the expected value based on mode

### Expected Behavior:
- Mode 0: MAX speed = current vehicle speed (original behavior)
- Mode 1: MAX speed = detected speed limit
- Mode 2: MAX speed = detected speed limit × 1.10
- Mode 3: MAX speed = detected speed limit × 1.20

## Notes

- The feature only works when speed limit data is available (from map data or camera detection)
- If no speed limit is detected, the system falls back to current speed mode
- The cruise speed is clamped between minimum (8 km/h) and maximum (145 km/h) values
- The setting persists across reboots (PERSISTENT | BACKUP flag)

## Future Enhancements

Possible improvements:
1. Add offset customization (e.g., +5 mph, +10 mph instead of percentages)
2. Add visual indicator on HUD showing which mode is active
3. Add speed limit display on HUD
4. Add per-road-type settings (e.g., different offsets for highway vs city)
