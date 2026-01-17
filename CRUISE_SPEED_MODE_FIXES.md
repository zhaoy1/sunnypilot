# Cruise Speed Mode - Fallback Logic Fix

## Issue
When speed limit data is not available, the system needs to fall back to cluster speed instead of current vehicle speed.

## Solution

### Fallback Logic (in `selfdrive/car/cruise.py`)

The `initialize_v_cruise()` method now implements proper fallback logic:

1. **Mode 0 (Cluster Speed)**:
   - Primary: Use cluster speed from `CS.cruiseState.speed`
   - Fallback: If cluster speed is 0, use current vehicle speed `CS.vEgo`

2. **Modes 1-3 (Speed Limit Based)**:
   - Primary: Use speed limit with offset (10%, 20%)
   - Fallback: If no speed limit data (`speed_from_limit <= 0`), use cluster speed
   - Final fallback: If cluster speed is also 0, use current vehicle speed

### Speed Sources

1. **Cluster Speed**: `CS.cruiseState.speed`
   - Comes from vehicle's instrument cluster
   - Set in `carstate.py` from `cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"]`
   - Converted to m/s based on cluster units (kph or mph)
   - Represents the speed the driver sees on their dashboard

2. **Current Vehicle Speed**: `CS.vEgo`
   - Actual vehicle speed from ESP/wheel sensors
   - May differ slightly from cluster speed
   - Used as final fallback when cluster speed is unavailable

3. **Speed Limit**: `self.speed_limit_kph`
   - Comes from map data via `liveMapDataSP`
   - Updated in `card.py` when valid speed limit data is available
   - Only used in modes 1-3

### Rivian-Specific Features

All modes respect Rivian's cruise speed limits:
- Minimum: 20 mph (32.2 kph)
- Maximum: 85 mph (136.8 kph)

For modes 1-3, the system uses `max(current_speed, speed_limit_with_offset)` to allow the driver to go faster than the speed limit if desired.

## Code Flow

```
initialize_v_cruise() called when cruise is engaged
  ↓
Read cruise_speed_mode from file
  ↓
Get cluster_speed from CS.cruiseState.speed
  ↓
Mode 0: Use cluster_speed (or current_speed if cluster unavailable)
Mode 1-3 with speed limit: Use max(current_speed, speed_limit_with_offset)
Mode 1-3 without speed limit: Fall back to cluster_speed (or current_speed)
  ↓
Apply Rivian limits (20-85 mph)
  ↓
Set v_cruise_kph
```

## Testing

To verify the fallback logic works:

1. **Test Mode 0**: Should always use cluster speed
2. **Test Modes 1-3 with speed limit**: Should use speed limit with offset
3. **Test Modes 1-3 without speed limit**: Should fall back to cluster speed
4. **Test with no cluster data**: Should fall back to current vehicle speed

## Related Files

- `selfdrive/car/cruise.py`: Cruise speed calculation logic
- `selfdrive/car/card.py`: Speed limit subscription and updates
- `opendbc_repo/opendbc/car/rivian/carstate.py`: Cluster speed source
