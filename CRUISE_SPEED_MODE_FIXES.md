# Cruise Speed Mode - Review Fixes

## Issues Addressed

### Issue 1: CruiseSpeedMode param is only read once
**Problem**: Mode was only read in `__init__()`, so changing the setting in UI wouldn't take effect until restart.

**Fix**: Added `self.read_cruise_speed_mode()` call at the start of `initialize_v_cruise()`.

**File**: `selfdrive/car/cruise.py`
```python
def initialize_v_cruise(self, CS, experimental_mode: bool, dynamic_experimental_control: bool) -> None:
    # initializing is handled by the PCM
    if self.CP.pcmCruise:
      return

    # Re-read cruise speed mode to pick up any changes from Settings UI
    self.read_cruise_speed_mode()  # <-- NEW: Read mode on every cruise engagement

    # ... rest of method
```

**Result**: Mode is now re-read every time cruise is engaged, so Settings changes take effect immediately.

---

### Issue 2: Speed limit validity check should be stricter
**Problem**: Code checked `speedLimitValid` but not `speedLimit > 0`, could accept zero or stale values.

**Fix**: Added explicit check for `speed_limit_ms > 0` before calling `update_speed_limit()`.

**File**: `selfdrive/car/card.py`
```python
# Update speed limit from roadLimitSpeed for cruise speed mode
# Speed limits come from map data in m/s and are converted to kph for internal use,
# independent of UI metric/imperial display units
if self.sm.valid['roadLimitSpeed'] and self.sm['roadLimitSpeed'].speedLimitValid:
  speed_limit_ms = self.sm['roadLimitSpeed'].speedLimit
  if speed_limit_ms > 0:  # <-- NEW: Ensure we have a valid positive speed limit
    self.v_cruise_helper.update_speed_limit(speed_limit_ms)
```

**Result**: Only positive, non-zero speed limits are accepted, preventing incorrect cruise initialization.

---

### Issue 3: Unit handling is correct but fragile
**Problem**: Unit conversion was correct but lacked documentation, risking future regressions.

**Fix**: Added comprehensive docstring to `update_speed_limit()` method explaining unit handling.

**File**: `selfdrive/car/cruise.py`
```python
def update_speed_limit(self, speed_limit_ms: float):
  """Update speed limit from roadLimitSpeed.

  Speed limits from roadLimitSpeed are always in m/s (from map data).
  We convert once to kph for internal cruise calculations.
  This is independent of UI metric/imperial display units.
  """
  self.speed_limit_kph = speed_limit_ms * CV.MS_TO_KPH if speed_limit_ms > 0 else 0.0
```

**Also added comment in card.py**:
```python
# Speed limits come from map data in m/s and are converted to kph for internal use,
# independent of UI metric/imperial display units
```

**Result**: Clear documentation prevents future confusion about unit handling and metric/imperial independence.

---

## Summary of Changes

| File | Change | Lines Modified |
|------|--------|----------------|
| `selfdrive/car/cruise.py` | Added `read_cruise_speed_mode()` call in `initialize_v_cruise()` | +3 |
| `selfdrive/car/cruise.py` | Enhanced docstring for `update_speed_limit()` | +5 |
| `selfdrive/car/card.py` | Added `speed_limit_ms > 0` check | +3 |
| `selfdrive/car/card.py` | Added clarifying comment about units | +2 |

**Total**: 13 lines added/modified

---

## Testing Recommendations

### Test 1: Mode changes without restart
1. Set mode to "Current Speed" in Settings
2. Enable cruise - verify it uses current speed
3. Disable cruise
4. Change mode to "Speed Limit" in Settings (without restarting)
5. Enable cruise again - verify it now uses speed limit
6. **Expected**: Mode change takes effect immediately

### Test 2: Zero speed limit handling
1. Set mode to "Speed Limit"
2. Drive in area with no speed limit data (speedLimit = 0)
3. Enable cruise
4. **Expected**: Falls back to current speed (doesn't set cruise to 0)

### Test 3: Stale speed limit handling
1. Set mode to "Speed Limit + 10%"
2. Drive from 65 mph zone to area with no speed limit
3. Enable cruise
4. **Expected**: Uses current speed, not stale 65 mph value

### Test 4: Unit consistency
1. Test in both metric (Canada) and imperial (US) regions
2. Verify speed limit detection works correctly in both
3. Verify cruise speed calculations are correct regardless of UI units
4. **Expected**: Speed limit from maps (m/s) → internal (kph) → display (kph or mph) works correctly

---

## Code Quality Improvements

1. **Robustness**: Mode is always fresh when cruise engages
2. **Safety**: Invalid speed limits (≤0) are rejected
3. **Maintainability**: Clear documentation prevents future bugs
4. **User Experience**: Settings changes take effect immediately without restart

All three issues have been addressed with minimal code changes and maximum clarity.
