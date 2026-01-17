# Cruise Speed Mode - Quick Reference

## What Was Done

Fixed the fallback logic so when speed limit data is not available, the system properly falls back to cluster speed instead of current vehicle speed.

## Changes Made

### 1. Fixed `selfdrive/car/cruise.py`
- Mode 0 now uses cluster speed (`CS.cruiseState.speed`)
- Modes 1-3 fall back to cluster speed when no speed limit available
- Cleaned up debug logging (less verbose)

### 2. Cleaned up `selfdrive/car/card.py`
- Removed debug prints
- Speed limit setting logic unchanged (already correct)

## How It Works Now

### Mode 0 (Cluster Speed)
```
1. Try cluster speed from instrument cluster
2. If cluster speed is 0, use current vehicle speed
```

### Modes 1-3 (Speed Limit Based)
```
1. Try speed limit with offset (10%, 20%)
2. If no speed limit, try cluster speed
3. If cluster speed is 0, use current vehicle speed
```

## Next Steps

### 1. Push Changes to GitHub
```bash
git add selfdrive/car/cruise.py selfdrive/car/card.py
git commit -m "Fix cruise speed mode fallback logic and cleanup logging"
git push origin dev
```

### 2. Update Device
```bash
ssh comma@192.168.1.54
cd /data/openpilot
git pull origin dev
sudo reboot
```

### 3. Test Speed Limit UI (After Reboot)
```bash
ssh comma@192.168.1.54
cd /data/openpilot
python3 test_speed_limit_flow.py
```

Watch the output while driving to see if speed limit data flows correctly.

## Expected Behavior

### When Driving
- **Mode 0**: Cruise speed = cluster speed (what you see on dashboard)
- **Mode 1**: Cruise speed = speed limit (or cluster if no limit)
- **Mode 2**: Cruise speed = speed limit + 10% (or cluster if no limit)
- **Mode 3**: Cruise speed = speed limit + 20% (or cluster if no limit)

### All Modes
- Minimum: 20 mph
- Maximum: 85 mph
- Gas pedal: Press gas while cruising to increase cruise speed
- Resume: Uses last cruise speed

## Troubleshooting

### Speed Limit Not Showing on UI
1. Run diagnostic script: `python3 test_speed_limit_flow.py`
2. Check if `liveMapDataSP` is publishing data
3. Check if `carStateSP.speedLimit` is set
4. Check if `longitudinalPlanSP` has speed limit

### Cruise Speed Not Using Speed Limit
1. Check mode setting in UI (Settings → Cruise)
2. Verify mode file: `cat /data/params/d/CruiseSpeedMode`
3. Check logs: `tmux capture-pane -pt comma:0 | grep CRUISE`

### Cruise Speed Too Low/High
- Check if within 20-85 mph limits
- Verify speed limit data is correct
- Check cluster speed reading

## Files Modified

1. `selfdrive/car/cruise.py` - Fallback logic and logging
2. `selfdrive/car/card.py` - Logging cleanup

## Documentation

- **IMPLEMENTATION_COMPLETE.md**: Full implementation details
- **CRUISE_SPEED_MODE_FIXES.md**: Fallback logic explanation
- **SPEED_LIMIT_UI_DIAGNOSTIC.md**: Speed limit troubleshooting
- **QUICK_REFERENCE.md**: This file
