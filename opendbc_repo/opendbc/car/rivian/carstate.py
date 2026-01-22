import copy
from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.interfaces import CarStateBase
from opendbc.car.rivian.values import DBC, GEAR_MAP
from opendbc.car.common.conversions import Conversions as CV
# from openpilot.common.params import Params
# from opendbc.sunnypilot.car.rivian.carstate_ext import CarStateExt

GearShifter = structs.CarState.GearShifter


class CarState(CarStateBase): #, CarStateExt):
  def __init__(self, CP, CP_SP):
    CarStateBase.__init__(self, CP, CP_SP)
    # CarStateExt.__init__(self, CP, CP_SP)
    self.last_speed = 30

    self.acm_lka_hba_cmd = None
    self.sccm_wheel_touch = None
    self.vdm_adas_status = None

    # Cruise speed mode for speed limit based cruise
    self.cruise_speed_mode = 0  # 0=cluster, 1=speed limit, 2=speed limit+10%, 3=speed limit+20%
    self.read_cruise_speed_mode()

  def read_cruise_speed_mode(self):
    """Read cruise speed mode from file"""
    try:
      with open("/data/params/d/CruiseSpeedMode", 'r') as f:
        self.cruise_speed_mode = int(f.read().strip())
    except (FileNotFoundError, ValueError):
      self.cruise_speed_mode = 0

  def update_cruise_speed_from_cs_sp(self, CS, CS_SP):
    """Update cruise speed based on speed limit in CS_SP and cruise speed mode.
    Called from card.py after CS_SP.speedLimit is set.
    """
    # Re-read cruise speed mode to pick up changes from Settings UI
    self.read_cruise_speed_mode()

    # Get speed limit from CS_SP and convert to kph
    speed_limit_ms = CS_SP.speedLimit
    speed_limit_kph = speed_limit_ms * CV.MS_TO_KPH if speed_limit_ms > 0 else 0.0

    # Get current speeds
    current_speed_kph = CS.vEgo * CV.MS_TO_KPH
    cluster_speed_kph = self.last_speed

    print(f"[CARSTATE] Mode: {self.cruise_speed_mode}, SpeedLimit: {speed_limit_kph:.1f} kph (from CS_SP: {speed_limit_ms:.1f} m/s), Current: {current_speed_kph:.1f} kph, Cluster: {cluster_speed_kph:.1f} kph")

    # Calculate cruise speed based on mode
    if self.cruise_speed_mode == 0:
      # Mode 0: Use cluster speed
      cruise_speed_kph = cluster_speed_kph
      print(f"[CARSTATE] Mode 0 - Using cluster speed: {cruise_speed_kph:.1f} kph")
    elif speed_limit_kph > 0:
      # Modes 1-3: Use speed limit with offset
      if self.cruise_speed_mode == 1:  # Speed limit
        speed_from_limit = speed_limit_kph
      elif self.cruise_speed_mode == 2:  # Speed limit + 10%
        speed_from_limit = speed_limit_kph * 1.10
      elif self.cruise_speed_mode == 3:  # Speed limit + 20%
        speed_from_limit = speed_limit_kph * 1.20
      else:
        speed_from_limit = cluster_speed_kph

      # Choose max between current speed and speed limit (with offset)
      cruise_speed_kph = max(current_speed_kph, speed_from_limit)
      print(f"[CARSTATE] Mode {self.cruise_speed_mode} - Speed from limit: {speed_from_limit:.1f} kph, Final: {cruise_speed_kph:.1f} kph")
    else:
      # Modes 1-3 but no speed limit: Fall back to cluster speed
      cruise_speed_kph = cluster_speed_kph
      print(f"[CARSTATE] Mode {self.cruise_speed_mode} - No speed limit, using cluster: {cruise_speed_kph:.1f} kph")

    # Apply Rivian-specific limits (20-85 mph) and set cruise speed
    cruise_speed_kph_limited = max(20 * CV.MPH_TO_KPH, min(cruise_speed_kph, 85 * CV.MPH_TO_KPH))
    cruise_speed_ms = cruise_speed_kph_limited * CV.KPH_TO_MS
    CS.cruiseState.speed = cruise_speed_ms
    print(f"[CARSTATE] Final cruise speed: {cruise_speed_kph_limited:.1f} kph ({cruise_speed_ms:.1f} m/s)")

  def update(self, can_parsers) -> tuple[structs.CarState, structs.CarStateSP]:
    cp = can_parsers[Bus.pt]
    cp_cam = can_parsers[Bus.cam]
    cp_adas = can_parsers[Bus.adas]
    ret = structs.CarState()
    ret_sp = structs.CarStateSP()

    # Vehicle speed
    ret.vEgoRaw = cp.vl["ESP_Status"]["ESP_Vehicle_Speed"] * CV.KPH_TO_MS
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = abs(ret.vEgoRaw) < 0.01
    conversion = CV.KPH_TO_MS if cp_adas.vl["Cluster"]["Cluster_Unit"] == 0 else CV.MPH_TO_MS
    ret.vEgoCluster = cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"] * conversion

    # Gas pedal
    ret.gasPressed = cp.vl["VDM_PropStatus"]["VDM_AcceleratorPedalPosition"] > 0

    # Brake pedal
    ret.brake = cp.vl["ESPiB3"]["ESPiB3_pMC1"] / 250.0  # pressure in Bar
    ret.brakePressed = cp.vl["iBESP2"]["iBESP2_BrakePedalApplied"] == 1

    # Steering wheel
    ret.steeringAngleDeg = cp.vl["EPAS_AdasStatus"]["EPAS_InternalSas"]
    ret.steeringRateDeg = cp.vl["EPAS_AdasStatus"]["EPAS_SteeringAngleSpeed"]
    ret.steeringTorque = cp.vl["EPAS_SystemStatus"]["EPAS_TorsionBarTorque"]
    ret.steeringPressed = self.update_steering_pressed(abs(ret.steeringTorque) > 1.0, 5)

    ret.steerFaultTemporary = cp.vl["EPAS_AdasStatus"]["EPAS_EacErrorCode"] != 0

    # Cruise state
    ret.cruiseState.enabled = cp_cam.vl["ACM_Status"]["ACM_FeatureStatus"] == 1

    # Track cluster speed for cruise control
    if not ret.cruiseState.enabled:
      cluster_speed = int(cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"])
      self.last_speed = cluster_speed
    elif ret.gasPressed:
      cluster_speed = cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"]
      self.last_speed = max(cluster_speed, self.last_speed)

    ret.cruiseState.available = True  # cp.vl["VDM_AdasSts"]["VDM_AdasInterfaceStatus"] == 1
    ret.cruiseState.standstill = cp.vl["VDM_AdasSts"]["VDM_AdasVehicleHoldStatus"] == 1

    # ACM_Status->ACM_FaultSupervisorState normally 1, appears to go to 3 when either:
    # 1. car in park/not in drive (normal)
    # 2. something (message from another ECU) ACM relies on is faulty
    #  * ACM_FaultStatus will stay 0 since ACM itself isn't faulted
    # TODO: ACM_FaultStatus hasn't been seen high yet, but log anyway
    ret.accFaulted = (cp_cam.vl["ACM_Status"]["ACM_FaultStatus"] == 1 or
                      # VDM_AdasFaultStatus=Brk_Intv is the default for some reason
                      # VDM_AdasFaultStatus=Cntr_Fault isn't fully understood, but we've seen it in the wild
                      # VDM_AdasFaultStatus=Imps_Cmd was seen when sending it rapidly changing ACC enable commands, or when ACC command drops out
                      cp.vl["VDM_AdasSts"]["VDM_AdasFaultStatus"] in (2, 3))  # 2=Cntr_Fault, 3=Imps_Cmd

    # Gear
    ret.gearShifter = GEAR_MAP.get(int(cp.vl["VDM_PropStatus"]["VDM_Prndl_Status"]), GearShifter.unknown)

    # Doors
    ret.doorOpen = any(cp_adas.vl["IndicatorLights"][door] != 2 for door in ("RearDriverDoor", "FrontPassengerDoor", "DriverDoor", "RearPassengerDoor"))

    # Blinkers
    ret.leftBlinker = cp_adas.vl["IndicatorLights"]["TurnLightLeft"] in (1, 2)
    ret.rightBlinker = cp_adas.vl["IndicatorLights"]["TurnLightRight"] in (1, 2)

    # Seatbelt
    ret.seatbeltUnlatched = cp.vl["RCM_Status"]["RCM_Status_IND_WARN_BELT_DRIVER"] != 0

    # Blindspot
    # ret.leftBlindspot = False
    # ret.rightBlindspot = False

    # AEB
    ret.stockAeb = cp_cam.vl["ACM_AebRequest"]["ACM_EnableRequest"] != 0

    # Messages needed by carcontroller
    self.acm_lka_hba_cmd = copy.copy(cp_cam.vl["ACM_lkaHbaCmd"])
    self.sccm_wheel_touch = copy.copy(cp.vl["SCCM_WheelTouch"])
    self.vdm_adas_status = copy.copy(cp.vl["VDM_AdasSts"])

    # CarStateExt.update(self, ret, can_parsers)

    return ret, ret_sp

  @staticmethod
  def get_can_parsers(CP, CP_SP):
    return {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 0),
      Bus.adas: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 1),
      Bus.cam: CANParser(DBC[CP.carFingerprint][Bus.pt], [], 2),
      # **CarStateExt.get_parser(CP, CP_SP),
    }