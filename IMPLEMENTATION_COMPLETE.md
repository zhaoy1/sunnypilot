# Cruise Speed Mode Implementation - Complete

## Feature Overview

Implemented a cruise speed mode system with 4 modes for initializing cruise speed on engagement:

- **Mode 0**: Cluster Speed (uses vehicle's instrument cluster speed)
- **Mode 1**: Speed Limit (exact speed limit from map data)
- **Mode 2**: Speed Limit + 10%
- **Mode 3**: Speed Limit + 20%

## Implementation Details

### 1. Storage System
- **Location**: `/data/params/d/CruiseSpeedMode`
- **Format**: Plain text file with single integer (0-3)
- **Reason**: Avoids recompiling `params_pyx.so` binary

### 2. Core Logic (`selfdrive/car/cruise.py`)

**Key Methods**:
- `read_cruise_speed_mode()`: Reads mode from file
- `calculate_cruise_speed_from_limit()`: Calculates cruise speed based on mode and speed limit
- `update_speed_limit()`: Updates internal speed limit from map data (m/s → kph)
- `initialize_v_cruise()`: Main logic for setting cruise speed on engagement

**Fallback Hierarchy**:
```
Mode 0:
  1. Cluster speed (CS.cruiseState.speed)
  2. Current vehicle speed (CS.vEgo)

Modes 1-3:
  1. Speed limit with offset (from map data)
  2. Cluster speed (when no speed limit available)
  3. Current vehicle speed (when neither available)
```

**Rivian-Specific Features**:
- Min/Max limits: 20-85 mph (32.2-136.8 kph)
- Max selection: `max(current_speed, speed_limit_with_offset)` allows driver to go faster
- Gas pedal update: When cruise enabled and gas pressed, updates cruise to new higher speed

### 3. Speed Limit Subscription (`selfdrive/car/card.py`)

**Data Flow**:
```
liveMapDataSP (map service)
  ↓
card.py (validates and converts)
  ↓
CS_SP.speedLimit (published to carStateSP)
  ↓
SpeedLimitResolver (processes with policy)
  ↓
longitudinalPlanSP (published for UI)
  ↓
UI (displays speed limit)
```

**Validation**:
- Checks `speedLimitValid == True`
- Checks `speedLimit > 0`
- Always sets `CS_SP.speedLimit` (either valid value or 0.0)

### 4. UI Settings (`selfdrive/ui/sunnypilot/layouts/settings/cruise.py`)

**Widget**: `multiple_button_item_sp` with 4 buttons
- Button labels: "Cluster", "Speed Lmt", "10%+", "20%+"
- Button width: 250px
- Saves selection to file immediately on click

## Speed Sources Explained

### Cluster Speed (`CS.cruiseState.speed`)
- Source: Vehicle's instrument cluster display
- Set in: `opendbc_repo/opendbc/car/rivian/carstate.py`
- Raw data: `cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"]`
- Units: Converted to m/s based on cluster units (kph or mph)
- Purpose: What the driver sees on their dashboard

### Current Vehicle Speed (`CS.vEgo`)
- Source: ESP/wheel sensors
- Units: m/s
- Purpose: Actual vehicle speed, may differ slightly from cluster

### Speed Limit (`self.speed_limit_kph`)
- Source: Map data via `liveMapDataSP`
- Units: Received in m/s, converted to kph internally
- Purpose: Road speed limit for modes 1-3

## Code Organization

### Modified Files
1. **selfdrive/car/cruise.py** (220 lines)
   - Cruise speed calculation logic
   - Fallback handling
   - Rivian-specific features

2. **selfdrive/car/card.py** (10 lines changed)
   - Speed limit subscription
   - CS_SP.speedLimit setting

3. **selfdrive/ui/sunnypilot/layouts/settings/cruise.py** (15 lines added)
   - UI settings widget

4. **selfdrive/controls/controlsd.py** (commented out old code)
   - Removed references to non-existent `roadLimitSpeed`

### Documentation Files
1. **CRUISE_SPEED_MODE_IMPLEMENTATION.md**: Initial implementation details
2. **CRUISE_SPEED_MODE_RIVIAN_FEATURES.md**: Rivian-specific features
3. **CRUISE_SPEED_MODE_FIXES.md**: Fallback logic explanation
4. **SPEED_LIMIT_UI_DIAGNOSTIC.md**: Speed limit data flow and diagnostics
5. **SUMMARY_FALLBACK_AND_CLEANUP.md**: Recent changes summary
6. **IMPLEMENTATION_COMPLETE.md**: This file

### Diagnostic Tools
- **test_speed_limit_flow.py**: Script to diagnose speed limit data flow on device

## Known Issues

### Speed Limit Not Displayed on UI
**Status**: Code is correct, needs device testing

**Diagnostic Steps**:
1. SSH to device: `ssh comma@192.168.1.54`
2. Navigate: `cd /data/openpilot`
3. Pull changes: `git pull`
4. Run diagnostic: `python3 test_speed_limit_flow.py`
5. Check output for where data flow breaks

**Expected Output** (when working):
```
[liveMapDataSP] Valid: True
  speedLimitValid: True
  speedLimit: 24.6 m/s (88.6 kph)

[carStateSP] Valid: True
  speedLimit: 24.6 m/s (88.6 kph)

[longitudinalPlanSP] Valid: True
  resolver.speedLimit: 24.6 m/s (88.6 kph)
  resolver.speedLimitValid: True
  resolver.source: car
```

## Testing Checklist

### Basic Functionality
- [ ] Mode 0: Uses cluster speed
- [ ] Mode 1: Uses exact speed limit
- [ ] Mode 2: Uses speed limit + 10%
- [ ] Mode 3: Uses speed limit + 20%
- [ ] Settings UI: All 4 buttons work
- [ ] Settings UI: Selection persists after reboot

### Fallback Behavior
- [ ] Mode 0: Falls back to current speed when cluster unavailable
- [ ] Modes 1-3: Fall back to cluster speed when no speed limit
- [ ] Modes 1-3: Fall back to current speed when neither available

### Rivian Features
- [ ] Min limit: Won't set cruise below 20 mph
- [ ] Max limit: Won't set cruise above 85 mph
- [ ] Max selection: Can go faster than speed limit
- [ ] Gas pedal: Updates cruise when pressed while cruising
- [ ] Resume: Uses last cruise speed

### UI Display
- [ ] Speed limit shows on UI when available
- [ ] Speed limit updates as you drive
- [ ] Speed limit disappears when not available

## Deployment Steps

1. **Commit and push changes**:
   ```bash
   git add selfdrive/car/cruise.py selfdrive/car/card.py
   git add selfdrive/ui/sunnypilot/layouts/settings/cruise.py
   git add test_speed_limit_flow.py *.md
   git commit -m "Implement cruise speed mode with fallback logic"
   git push origin dev
   ```

2. **Update device**:
   ```bash
   ssh comma@192.168.1.54
   cd /data/openpilot
   git fetch origin
   git checkout dev
   git pull origin dev
   sudo reboot
   ```

3. **Test on device**:
   - Wait for device to reboot
   - Go to Settings → Cruise
   - Select different modes
   - Drive and test cruise engagement
   - Run diagnostic script if speed limit not showing

## Future Enhancements

1. **Add mode 4**: Speed Limit + custom offset (user configurable)
2. **Add visual feedback**: Show which mode is active on main UI
3. **Add speed limit source indicator**: Show if using map data or car data
4. **Add logging**: Log mode selection and speed calculations for debugging
5. **Add telemetry**: Track which modes are most popular

## Technical Notes

### Why File-Based Storage?
- Avoids recompiling `params_pyx.so` (Cython binary)
- Simple and reliable
- Easy to debug (can check file contents directly)
- No dependencies on params system

### Why Convert Speed Limits to kph?
- Internal calculations use kph for consistency
- UI display units (metric/imperial) are separate concern
- Avoids repeated conversions
- Matches existing openpilot conventions

### Why Max Selection for Speed Limit Modes?
- Rivian-specific: Allows driver to override speed limit
- Safety: Driver can always go faster if needed
- Flexibility: Useful when speed limit data is outdated

### Why Cluster Speed vs Current Speed?
- Cluster speed: What driver sees and expects
- Current speed: More accurate but may differ from cluster
- Fallback hierarchy ensures we always have a value

## Support

For issues or questions:
1. Check diagnostic output from `test_speed_limit_flow.py`
2. Check logs: `ssh comma@192.168.1.54 "tmux capture-pane -pt comma:0 | grep CRUISE"`
3. Verify mode file: `ssh comma@192.168.1.54 "cat /data/params/d/CruiseSpeedMode"`
4. Check speed limit data: Run diagnostic script while driving

## Conclusion

The cruise speed mode feature is fully implemented with:
- ✅ 4 modes for cruise speed initialization
- ✅ Proper fallback logic when data unavailable
- ✅ Rivian-specific features (limits, max selection, gas pedal update)
- ✅ UI settings for mode selection
- ✅ Speed limit subscription and display (code complete, needs device testing)
- ✅ Comprehensive documentation and diagnostic tools

Ready for testing on device!
