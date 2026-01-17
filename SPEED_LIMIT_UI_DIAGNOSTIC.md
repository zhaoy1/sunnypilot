# Speed Limit UI Display Diagnostic

## Problem
The UI is not showing speed limit information after our changes.

## Speed Limit Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Map Service                                                  │
│    Publishes: liveMapDataSP                                     │
│    Fields: speedLimit (m/s), speedLimitValid                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. card.py (100Hz)                                              │
│    Reads: liveMapDataSP.speedLimit                              │
│    Sets: CS_SP.speedLimit = speed_limit_ms                      │
│    Publishes: carStateSP                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SpeedLimitResolver (in longitudinal_planner.py)              │
│    Reads: carStateSP.speedLimit                                 │
│    Processes: Applies policy, offset, etc.                      │
│    Stores: self.speed_limit, self.speed_limit_valid            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LongitudinalPlanner.publish_longitudinal_plan_sp()           │
│    Reads: self.resolver.speed_limit                             │
│    Sets: longitudinalPlanSP.speedLimit.resolver.speedLimit      │
│    Publishes: longitudinalPlanSP                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. UI (Native C++ - precompiled)                                │
│    Reads: longitudinalPlanSP.speedLimit.resolver.speedLimit     │
│    Displays: Speed limit on screen                              │
└─────────────────────────────────────────────────────────────────┘
```

## Diagnostic Steps

### Step 1: Check if liveMapDataSP is being published

SSH to device and run:
```bash
cd /data/openpilot
python3 test_speed_limit_flow.py
```

This will show:
- Is `liveMapDataSP` being published?
- Is `speedLimitValid` true?
- What is the `speedLimit` value?

### Step 2: Check if carStateSP is receiving speed limit

The test script will also show:
- Is `carStateSP.speedLimit` being set?
- Does it match `liveMapDataSP.speedLimit`?

### Step 3: Check if longitudinalPlanSP is publishing speed limit

The test script will show:
- Is `longitudinalPlanSP.speedLimit.resolver.speedLimit` set?
- Is `speedLimitValid` true?
- What is the source?

### Step 4: Check debug logs

```bash
ssh comma@192.168.1.54 "tmux capture-pane -pt comma:0 | grep -E 'CARD|liveMapDataSP'"
```

Look for:
- `[CARD] Speed limit from liveMapDataSP: X m/s`
- `[CARD] liveMapDataSP not valid`
- `[CARD] speedLimitValid is False`

## Possible Issues

### Issue 1: liveMapDataSP not being published
**Symptom**: Test script shows no `liveMapDataSP` updates
**Cause**: Map service (mapd) not running or no GPS fix
**Solution**:
- Check if mapd process is running
- Check GPS status
- Drive on a road with known speed limits

### Issue 2: speedLimitValid is False
**Symptom**: `liveMapDataSP` exists but `speedLimitValid = False`
**Cause**: No speed limit data for current location
**Solution**: Drive on a road with speed limits in map database

### Issue 3: carStateSP.speedLimit is 0
**Symptom**: `liveMapDataSP` has data but `carStateSP.speedLimit = 0`
**Cause**: Our code in card.py not setting it correctly
**Solution**: Check debug logs, verify code logic

### Issue 4: longitudinalPlanSP not publishing speed limit
**Symptom**: `carStateSP` has data but `longitudinalPlanSP` doesn't
**Cause**: SpeedLimitResolver not reading carStateSP correctly
**Solution**: Check SpeedLimitResolver policy settings

### Issue 5: UI not reading longitudinalPlanSP
**Symptom**: All messages have correct data but UI shows nothing
**Cause**: UI code issue (precompiled, can't fix)
**Solution**: May need to use different UI or wait for sunnypilot update

## Code Locations

### Where we set speed limit:
- `selfdrive/car/card.py` line ~230: `CS_SP.speedLimit = speed_limit_ms`

### Where resolver reads it:
- `openpilot/sunnypilot/selfdrive/controls/lib/speed_limit/speed_limit_resolver.py` line ~116:
  ```python
  self.limit_solutions[SpeedLimitSource.car] = sm['carStateSP'].speedLimit
  ```

### Where planner publishes it:
- `openpilot/sunnypilot/selfdrive/controls/lib/longitudinal_planner.py` line ~124:
  ```python
  resolver.speedLimit = float(self.resolver.speed_limit)
  resolver.speedLimitValid = self.resolver.speed_limit_valid
  ```

## Expected Values

When working correctly, you should see:
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

## Next Steps

1. Run the diagnostic script on the device
2. Share the output
3. Check which step in the flow is failing
4. Fix the specific issue based on diagnostic results
