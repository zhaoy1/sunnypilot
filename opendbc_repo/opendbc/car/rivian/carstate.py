import copy
from opendbc.can import CANParser
from opendbc.car import Bus, structs
from opendbc.car.interfaces import CarStateBase
from opendbc.car.rivian.values import DBC, GEAR_MAP
from opendbc.car.common.conversions import Conversions as CV
from openpilot.common.params import Params
import selfdrive.messaging as messaging

# from opendbc.sunnypilot.car.rivian.carstate_ext import CarStateExt

GearShifter = structs.CarState.GearShifter


class CarState(CarStateBase): #, CarStateExt):
  def __init__(self, CP, CP_SP):
    CarStateBase.__init__(self, CP, CP_SP)
    # CarStateExt.__init__(self, CP, CP_SP)
    self.last_speed = 20

    self.acm_lka_hba_cmd = None
    self.sccm_wheel_touch = None
    self.vdm_adas_status = None

    # create SubMaster (if not already created in this module)
    self.sm = messaging.SubMaster(['liveMapData', 'carState'])  # add other channels you already use


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

    # Live Map data: check that the message is present and contains a valid speed limit
    # field names vary slightly across forks/versions; try the common ones below
    self.sm.update()
    lmd = self.sm['liveMapData']
    speed_limit = 0
    speed_limit_valid = False

    # common field names you might see:
    # lmd.speedLimit (int, usually km/h) and lmd.speedLimitValid (bool)
    # or lmd.speedLimitKm/h etc. — use getattr() to be robust

    if lmd.valid:  # top-level validity flag for the message
      # try common attributes safely
      if hasattr(lmd, 'speedLimit') and lmd.speedLimit > 0:
        speed_limit = lmd.speedLimit
        # many implementations also have a boolean flag:
        speed_limit_valid = getattr(lmd, 'speedLimitValid', True)
      else:
        # try alternative name(s) if present
        speed_limit = getattr(lmd, 'speed_limit', None) or getattr(lmd, 'speedLimitKph', None)
        if speed_limit is not None:
          speed_limit_valid = True

    # --- read and adjust TSR speed ---
    #tsr_speed = int(cp_adas.vl["ACM_tsrCmd"]["ACM_tsrSpdDisClsMain"])

    # Apply mapping or keep as-is if not listed
    # adjusted_tsr_speed = speed_adjust_map.get(tsr_speed, tsr_speed)
    speed_adjust_map = {
      35: 42,
      40: 46,
      60: 68,
      70: 78,
      100: 110
    }

    adjusted_tsr_speed = speed_adjust_map.get(speed_limit, speed_limit)

    # --- read parameter and button action ---
    params = Params()
    use_tsr = params.get_bool("UseTSRAsCruiseSpeed")

    try:
      delta = int(params.get("CruiseSpeedDelta") or b"0")
    except Exception:
      delta = 0

    # --- determine base speed ---
    if not ret.cruiseState.enabled:
      cluster_speed = int(cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"])
      if use_tsr:
        self.last_speed = max(adjusted_tsr_speed, cluster_speed)
      else:
        self.last_speed = cluster_speed

    elif ret.gasPressed:
      cluster_speed = cp_adas.vl["Cluster"]["Cluster_VehicleSpeed"]
      self.last_speed = max(cluster_speed, self.last_speed)

    # --- apply delta from + / – buttons ---
    if delta != 0:
      self.last_speed += delta
      params.put("CruiseSpeedDelta", "0")  # reset after applying

    # --- final cruise speed ---
    ret.cruiseState.speed = max(
      20 * CV.MPH_TO_MS,
      min(self.last_speed * conversion, 85 * CV.MPH_TO_MS)
    )

    if not self.CP.openpilotLongitudinalControl:
      ret.cruiseState.speed = -1
    ret.cruiseState.available = True  # cp.vl["VDM_AdasSts"]["VDM_AdasInterfaceStatus"] == 1
    ret.cruiseState.standstill = cp.vl["VDM_AdasSts"]["VDM_AdasVehicleHoldStatus"] == 1

    # TODO: log ACM_Unkown2=3 as a fault. need to filter it at the start and end of routes though
    # ACM_FaultStatus hasn't been seen yet
    ret.accFaulted = (cp_cam.vl["ACM_Status"]["ACM_FaultStatus"] == 1 or
                      # VDM_AdasFaultStatus=Brk_Intv is the default for some reason
                      # VDM_AdasFaultStatus=Imps_Cmd was seen when sending it rapidly changing ACC enable commands
                      # VDM_AdasFaultStatus=Cntr_Fault isn't fully understood, but we've seen it in the wild
                      cp.vl["VDM_AdasSts"]["VDM_AdasFaultStatus"] in (3,))  # 3=Imps_Cmd
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
