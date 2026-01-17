# Rivian-Specific Cruise Speed Mode Features

## Overview
Enhanced cruise speed mode with Rivian-specific behaviors for better integration with the vehicle's characteristics.

## Features Implemented

### 1. **Speed Limits (20-85 mph)**
- **Minimum**: 20 mph (32.2 kph)
- **Maximum**: 85 mph (136.8 kph)
- Applied to all cruise speed calculations
- Prevents setting cruise speed outside safe operating range

```python
self.cruise_min_kph = 20 * CV.MPH_TO_KPH  # 20 mph minimum
self.cruise_max_kph = 85 * CV.MPH_TO_KPH  # 85 mph maximum
```

### 2. **Max of Current Speed vs Speed Limit**
When cruise speed mode is set to use speed limit (modes 1-3):
- Calculates target speed from speed limit + offset
- Compares with current vehicle speed
- **Uses the HIGHER value**

**Example:**
- Speed limit: 55 mph
- Mode: Speed Limit + 10% = 60.5 mph
- Current speed: 65 mph
- **Result**: Cruise sets to 65 mph (respects driver's choice to go faster)

```python
if speed_from_limit > 0 and self.cruise_speed_mode > 0:
    # Choose max between current speed and speed limit (with offset)
    cruise_speed_kph = max(current_speed_kph, speed_from_limit)
```

### 3. **Gas Pedal Updates Cruise Speed**
When cruise control is **already engaged**:
- Driver presses gas pedal to accelerate
- System detects speed increase
- **Automatically updates cruise speed** to new higher speed
- Only updates if within 20-85 mph limits
- Only updates if new speed is higher than current cruise speed

**Example:**
- Cruise set to 60 mph
- Driver presses gas, accelerates to 70 mph
- **Result**: Cruise automatically updates to 70 mph
- Driver releases gas, car maintains 70 mph

```python
if _enabled and CS.gasPressed and CS.vEgo > 0:
    current_speed_kph = CS.vEgo * CV.MS_TO_KPH
    if self.cruise_min_kph <= current_speed_kph <= self.cruise_max_kph:
        if current_speed_kph > self.v_cruise_kph:
            self.v_cruise_kph = int(round(current_speed_kph))
```

## Cruise Speed Mode Behaviors

### Mode 0: Current Speed (Default)
- Uses current vehicle speed when engaging cruise
- Applies 20-85 mph limits
- Gas pedal updates work

### Mode 1: Speed Limit
- Target = Speed Limit
- Uses max(current_speed, speed_limit)
- Applies 20-85 mph limits
- Gas pedal updates work

### Mode 2: Speed Limit + 10%
- Target = Speed Limit × 1.10
- Uses max(current_speed, speed_limit × 1.10)
- Applies 20-85 mph limits
- Gas pedal updates work

### Mode 3: Speed Limit + 20%
- Target = Speed Limit × 1.20
- Uses max(current_speed, speed_limit × 1.20)
- Applies 20-85 mph limits
- Gas pedal updates work

## Example Scenarios

### Scenario 1: Speed Limit Mode on Highway
```
Speed Limit: 65 mph
Mode: Speed Limit (Mode 1)
Current Speed: 70 mph

When engaging cruise:
- Calculated from limit: 65 mph
- Current speed: 70 mph
- Result: max(65, 70) = 70 mph ✓
```

### Scenario 2: Speed Limit + 10% in City
```
Speed Limit: 35 mph
Mode: Speed Limit + 10% (Mode 2)
Current Speed: 30 mph

When engaging cruise:
- Calculated from limit: 35 × 1.10 = 38.5 mph
- Current speed: 30 mph
- Result: max(38.5, 30) = 38.5 mph ✓
```

### Scenario 3: Gas Pedal Acceleration
```
Cruise engaged at: 60 mph
Driver presses gas to: 75 mph

While gas pressed:
- System detects: 75 mph > 60 mph
- Within limits: 20 ≤ 75 ≤ 85 ✓
- Updates cruise to: 75 mph ✓

Driver releases gas:
- Car maintains: 75 mph ✓
```

### Scenario 4: Speed Limit Too Low
```
Speed Limit: 15 mph (school zone)
Mode: Speed Limit (Mode 1)
Current Speed: 25 mph

When engaging cruise:
- Calculated from limit: 15 mph
- Current speed: 25 mph
- Result: max(15, 25) = 25 mph
- After limits: max(20, 25) = 25 mph ✓
```

### Scenario 5: Speed Limit Too High
```
Speed Limit: 75 mph
Mode: Speed Limit + 20% (Mode 3)
Current Speed: 80 mph

When engaging cruise:
- Calculated from limit: 75 × 1.20 = 90 mph
- Current speed: 80 mph
- Result: max(90, 80) = 90 mph
- After limits: min(90, 85) = 85 mph ✓
```

## Debug Logging

All cruise speed calculations include detailed logging:

```
[CRUISE] initialize_v_cruise called - Mode: 2, Speed limit: 88.5 kph
[CRUISE] CS.vEgo: 96.6 kph, v_cruise_initialized: False
[CRUISE] Current speed: 96.6 kph, Speed from limit: 97.4 kph
[CRUISE] Using max of current speed and speed limit: 97.4 kph
[CRUISE] After applying limits (32.2-136.8 kph): 97 kph
[CRUISE] Final cruise speed set to: 97 kph
```

```
[CRUISE] Gas pressed while cruising, updating cruise speed to: 112 kph
```

## Testing Checklist

- [ ] Engage cruise at various speeds (verify 20-85 mph limits)
- [ ] Test Mode 1 (Speed Limit) with current speed > limit
- [ ] Test Mode 2 (Speed Limit + 10%) with current speed < limit
- [ ] Test Mode 3 (Speed Limit + 20%) with current speed > limit
- [ ] Press gas while cruising, verify cruise speed updates
- [ ] Test in school zone (15 mph limit) - should use 20 mph minimum
- [ ] Test on highway (75 mph limit) with +20% - should cap at 85 mph
- [ ] Check debug logs for all scenarios

## Files Modified

- `selfdrive/car/cruise.py`: Added Rivian-specific cruise logic
  - Min/max speed limits (20-85 mph)
  - Max of current speed vs speed limit calculation
  - Gas pedal cruise speed update
  - Enhanced debug logging

## Benefits

1. **Safety**: Hard limits prevent unsafe cruise speeds
2. **Flexibility**: Driver can choose to go faster than speed limit
3. **Convenience**: Gas pedal automatically updates cruise speed
4. **Transparency**: Detailed logging for debugging
5. **Consistency**: Behavior matches Rivian driver expectations
