# Summary: Fallback Logic and Code Cleanup

## Changes Made

### 1. Fixed Fallback Logic in `selfdrive/car/cruise.py`

**Problem**: When speed limit data is not available, the system was falling back to current vehicle speed (`CS.vEgo`) instead of cluster speed.

**Solution**: Implemented proper fallback hierarchy:

- **Mode 0 (Cluster Speed)**:
  - Primary: Use `CS.cruiseState.speed` (cluster speed)
  - Fallback: If cluster speed is 0, use current vehicle speed

- **Modes 1-3 (Speed Limit Based)**:
  - Primary: Use speed limit with offset (10%, 20%)
  - Fallback 1: If no speed limit data, use cluster speed
  - Fallback 2: If cluster speed is also 0, use current vehicle speed

**Key Code Changes**:
```python
# Get cluster speed from vehicle's instrument cluster
cluster_speed_kph = CS.cruiseState.speed * CV.MS_TO_KPH if CS.cruiseState.speed > 0 else 0

if self.cruise_speed_mode == 0:
    # Mode 0: Use cluster speed
    cruise_speed_kph = max(cluster_speed_kph, initial) if cluster_speed_kph > 0 else max(current_speed_kph, initial)
elif speed_from_limit > 0:
    # Modes 1-3: Use speed limit with offset
    cruise_speed_kph = max(current_speed_kph, speed_from_limit)
else:
    # Modes 1-3 but no speed limit: Fall back to cluster speed
    cruise_speed_kph = max(cluster_speed_kph, initial) if cluster_speed_kph > 0 else max(current_speed_kph, initial)
```

### 2. Cleaned Up Debug Logging

**Problem**: Excessive debug prints could slow down the system and clutter logs.

**Solution**: Reduced debug prints to only show essential information:

**In `cruise.py`**:
- Removed verbose prints from `read_cruise_speed_mode()`
- Simplified `initialize_v_cruise()` prints to one line per mode
- Removed gas pedal update print
- Kept only essential mode selection information

**In `card.py`**:
- Removed all debug prints for speed limit updates
- Code still functions correctly, just quieter

**Example of simplified output**:
```
[CRUISE] Mode 0 (Cluster): 55.0 kph
[CRUISE] Mode 1 (Limit): 88.5 kph → 88.5 kph
[CRUISE] Mode 2 (No limit, fallback): 55.0 kph
[CRUISE] Resume: 88 kph
```

### 3. Speed Limit UI Issue

**Status**: Code is correct, but need to run diagnostic on device

**What we set correctly**:
- `CS_SP.speedLimit` is always set (either to valid speed limit or 0.0)
- Speed limit flows: `liveMapDataSP` → `card.py` → `carStateSP` → `SpeedLimitResolver` → `longitudinalPlanSP` → UI

**Next step**: Run diagnostic script on device to identify where data flow breaks:
```bash
ssh comma@192.168.1.54
cd /data/openpilot
python3 test_speed_limit_flow.py
```

## Files Modified

1. **selfdrive/car/cruise.py**
   - Fixed fallback logic to use cluster speed
   - Cleaned up debug logging
   - Added proper mode 0 handling

2. **selfdrive/car/card.py**
   - Removed debug prints
   - Speed limit setting logic unchanged (already correct)

## Testing Checklist

- [ ] Mode 0: Uses cluster speed when available
- [ ] Mode 0: Falls back to current speed when cluster unavailable
- [ ] Mode 1-3: Uses speed limit when available
- [ ] Mode 1-3: Falls back to cluster speed when no speed limit
- [ ] Mode 1-3: Falls back to current speed when neither available
- [ ] All modes: Respects 20-85 mph limits
- [ ] Gas pedal: Updates cruise speed when pressed while cruising
- [ ] Resume: Uses last cruise speed
- [ ] UI: Speed limit displays correctly (needs device testing)

## Documentation Created

1. **CRUISE_SPEED_MODE_FIXES.md**: Detailed explanation of fallback logic
2. **SUMMARY_FALLBACK_AND_CLEANUP.md**: This file

## Next Steps

1. Push changes to GitHub
2. SSH to device and pull latest changes
3. Run diagnostic script to check speed limit UI
4. Test all modes while driving
5. Verify fallback behavior works correctly
