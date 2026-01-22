# Cruise Speed Mode - CarState Approach

## New Implementation Strategy

Instead of modifying the cruise control architecture (`pcmCruise` or `pcmCruiseSpeed`), we implement the cruise speed mode logic directly in `carstate.py` by updating `CS.cruiseState.speed` to include speed limit information.

## Why This Approach?

### **Problem Discovered**
Even with openpilot longitudinal control enabled, Rivian still uses the PCM cruise path:
```python
# In cruise.py
if not self.CP.pcmCruise or (not self.CP_SP.pcmCruiseSpeed and _enabled):
    # Use custom logic (non-PCM path)
else:
    # Use CS.cruiseState.speed directly (PCM path) ← Rivian uses this!
    self.v_cruise_kph = CS.cruiseState.speed * CV.MS_TO_KPH
```

### **Why PCM Path is Used**
- `self.CP.pcmCruise = True` (default for Rivian)
- `self.CP_SP.pcmCruiseSpeed = True` (default)
- Condition evaluates to `False`, so PCM path is taken

### **Benefits of CarState Approach**
1. **No architectural changes**: Keep existing cruise control logic intact
2. **Direct control**: `CS.cruiseState.speed` directly sets cruise speed
3. **Safer**: No risk of breaking other systems that depend on PCM flags
4. **Cleaner**: Logic is contained within Rivian-specific code

## Implementation Details

### **In `carstate.py`**

**Added cruise speed mode logic**:
```python
class CarState(CarStateBase):
  def __init__(self, CP, CP_SP):
    # ... existing code ...
    self.cruise_speed_mode = 0
    self.speed_limit_kph = 0.0
    self.read_cruise_speed_mode()

  def read_cruise_speed_mode(self):
    """Read cruise speed mode from file"""
    try:
      with open("/data/params/d/CruiseSpeedMode", 'r') as f:
        self.cruise_speed_mode = int(f.read().strip())
    except (FileNotFoundError, ValueError):
      self.cruise_speed_mode = 0

  def calculate_cruise_speed_from_limit(self, speed_limit_kph: float) -> float:
    """Calculate cruise speed based on speed limit and mode"""
    if self.cruise_speed_mode == 0:  # Cluster speed mode
      return 0.0
    elif self.cruise_speed_mode == 1:  # Speed limit
      return speed_limit_kph
    elif self.cruise_speed_mode == 2:  # Speed limit + 10%
      return speed_limit_kph * 1.10
    elif self.cruise_speed_mode == 3:  # Speed limit + 20%
      return speed_limit_kph * 1.20
    else:
      return 0.0
```

**Updated cruise speed calculation**:
```python
def update(self, can_parsers):
    # ... existing code ...

    # Re-read cruise speed mode to pick up changes from Settings UI
    self.read_cruise_speed_mode()

    # Calculate cruise speed based on mode
    current_speed_kph = ret.vEgo * CV.MS_TO_KPH
    cluster_speed_kph = self.last_speed
    speed_from_limit = self.calculate_cruise_speed_from_limit(self.speed_limit_kph)

    if self.cruise_speed_mode == 0:
      # Mode 0: Use cluster speed
      cruise_speed_kph = cluster_speed_kph
    elif speed_from_limit > 0:
      # Modes 1-3: Use speed limit with offset
      cruise_speed_kph = max(current_speed_kph, speed_from_limit)
    else:
      # Modes 1-3 but no speed limit: Fall back to cluster speed
      cruise_speed_kph = cluster_speed_kph

    # Apply Rivian limits and set cruise speed
    cruise_speed_kph = max(20 * CV.MPH_TO_KPH, min(cruise_speed_kph, 85 * CV.MPH_TO_KPH))
    ret.cruiseState.speed = cruise_speed_kph * CV.KPH_TO_MS
```

### **In `card.py`**

**Updated speed limit processing**:
```python
# Update speed limit from liveMapDataSP and recalculate cruise speed for Rivian
if self.sm.valid['liveMapDataSP'] and self.sm['liveMapDataSP'].speedLimitValid:
  speed_limit_ms = self.sm['liveMapDataSP'].speedLimit
  if speed_limit_ms > 0:
    CS_SP.speedLimit = speed_limit_ms  # For UI display

    # For Rivian: Update cruise speed based on speed limit and mode
    if self.CP.brand == 'rivian':
      self.CI.CS.speed_limit_kph = speed_limit_ms * CV.MS_TO_KPH
      # Recalculate cruise speed with updated speed limit
      # ... mode-based calculation ...
      CS.cruiseState.speed = cruise_speed_kph * CV.KPH_TO_MS
```

## Data Flow

```
1. carstate.py:update()
   ↓ Sets initial cruise speed based on cluster

2. card.py:state_update()
   ↓ Updates speed limit from liveMapDataSP
   ↓ Recalculates CS.cruiseState.speed with speed limit + mode

3. cruise.py:update_v_cruise()
   ↓ Uses CS.cruiseState.speed directly (PCM path)
   ↓ self.v_cruise_kph = CS.cruiseState.speed * CV.MS_TO_KPH
```

## Advantages

### **1. Direct Control**
- `CS.cruiseState.speed` directly becomes the cruise speed
- No dependency on cruise control architecture flags
- Immediate effect when speed limit or mode changes

### **2. Rivian-Specific**
- Logic contained within Rivian carstate code
- No impact on other car brands
- Maintains existing sunnypilot architecture

### **3. Real-Time Updates**
- Speed limit changes immediately affect cruise speed
- Mode changes picked up on next cruise engagement
- No need to restart or reload systems

### **4. Fallback Hierarchy**
- Mode 0: Cluster speed
- Modes 1-3 with speed limit: Speed limit + offset
- Modes 1-3 without speed limit: Cluster speed fallback

## Testing

### **Test Cases**
1. **Mode 0**: Should always use cluster speed
2. **Mode 1**: Should use exact speed limit when available
3. **Mode 2**: Should use speed limit + 10% when available
4. **Mode 3**: Should use speed limit + 20% when available
5. **No speed limit**: Modes 1-3 should fall back to cluster speed
6. **Speed limits**: All modes respect 20-85 mph limits
7. **Max selection**: Modes 1-3 use max(current_speed, speed_limit_with_offset)

### **Verification**
- Check `CS.cruiseState.speed` value in logs
- Verify cruise speed matches expected calculation
- Test mode switching in Settings UI
- Test speed limit availability/unavailability

## Files Modified

1. **opendbc_repo/opendbc/car/rivian/carstate.py**
   - Added cruise speed mode logic
   - Updated cruise speed calculation
   - Added speed limit processing

2. **selfdrive/car/card.py**
   - Updated speed limit processing for Rivian
   - Recalculate cruise speed after speed limit update
   - Added CV import

3. **selfdrive/ui/sunnypilot/layouts/settings/cruise.py**
   - UI settings (unchanged from previous implementation)

## Cleanup

### **Files No Longer Needed**
- Most of the cruise speed mode logic in `selfdrive/car/cruise.py` can be removed
- Speed limit processing in `cruise.py` can be simplified

### **What to Keep**
- UI settings in cruise.py settings
- Basic VCruiseHelper structure for compatibility
- Speed limit UI display logic

## Conclusion

This approach provides a cleaner, safer implementation of cruise speed modes by working with the existing cruise control architecture instead of against it. The logic is contained within Rivian-specific code and directly controls the cruise speed through `CS.cruiseState.speed`.