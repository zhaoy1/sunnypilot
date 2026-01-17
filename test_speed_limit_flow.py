#!/usr/bin/env python3
"""
Test script to diagnose speed limit data flow
Run this on the device to check if speed limit data is flowing correctly
"""
import cereal.messaging as messaging
import time

def main():
    print("=== Speed Limit Data Flow Diagnostic ===\n")

    # Subscribe to relevant messages
    sm = messaging.SubMaster(['liveMapDataSP', 'carStateSP', 'longitudinalPlanSP'])

    print("Waiting for messages... (Press Ctrl+C to stop)\n")

    try:
        while True:
            sm.update(1000)  # 1 second timeout

            # Check liveMapDataSP
            if sm.updated['liveMapDataSP']:
                map_data = sm['liveMapDataSP']
                print(f"[liveMapDataSP] Valid: {sm.valid['liveMapDataSP']}")
                print(f"  speedLimitValid: {map_data.speedLimitValid}")
                print(f"  speedLimit: {map_data.speedLimit} m/s ({map_data.speedLimit * 3.6:.1f} kph)")
                print()

            # Check carStateSP
            if sm.updated['carStateSP']:
                car_state_sp = sm['carStateSP']
                print(f"[carStateSP] Valid: {sm.valid['carStateSP']}")
                print(f"  speedLimit: {car_state_sp.speedLimit} m/s ({car_state_sp.speedLimit * 3.6:.1f} kph)")
                print()

            # Check longitudinalPlanSP
            if sm.updated['longitudinalPlanSP']:
                long_plan_sp = sm['longitudinalPlanSP']
                print(f"[longitudinalPlanSP] Valid: {sm.valid['longitudinalPlanSP']}")
                if hasattr(long_plan_sp, 'speedLimit'):
                    resolver = long_plan_sp.speedLimit.resolver
                    print(f"  resolver.speedLimit: {resolver.speedLimit} m/s ({resolver.speedLimit * 3.6:.1f} kph)")
                    print(f"  resolver.speedLimitValid: {resolver.speedLimitValid}")
                    print(f"  resolver.source: {resolver.source}")
                print()

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
