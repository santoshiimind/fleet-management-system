"""
OBD-II Reader — Communicates with vehicle ECU via OBD-II port.
Reads real-time parameters like RPM, speed, coolant temp, DTCs, etc.

In production, this connects to a real OBD-II adapter (ELM327).
For development, it uses the simulator fallback.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


# Standard OBD-II PIDs (Parameter IDs) — SAE J1979
OBD_PIDS = {
    "ENGINE_RPM":          {"pid": "010C", "bytes": 2, "formula": lambda a, b: ((a * 256) + b) / 4},
    "VEHICLE_SPEED":       {"pid": "010D", "bytes": 1, "formula": lambda a: a},
    "COOLANT_TEMP":        {"pid": "0105", "bytes": 1, "formula": lambda a: a - 40},
    "ENGINE_LOAD":         {"pid": "0104", "bytes": 1, "formula": lambda a: a * 100 / 255},
    "THROTTLE_POSITION":   {"pid": "0111", "bytes": 1, "formula": lambda a: a * 100 / 255},
    "INTAKE_AIR_TEMP":     {"pid": "010F", "bytes": 1, "formula": lambda a: a - 40},
    "MAF_RATE":            {"pid": "0110", "bytes": 2, "formula": lambda a, b: ((a * 256) + b) / 100},
    "FUEL_LEVEL":          {"pid": "012F", "bytes": 1, "formula": lambda a: a * 100 / 255},
    "FUEL_PRESSURE":       {"pid": "010A", "bytes": 1, "formula": lambda a: a * 3},
    "BATTERY_VOLTAGE":     {"pid": "0142", "bytes": 2, "formula": lambda a, b: ((a * 256) + b) / 1000},
    "OIL_TEMP":            {"pid": "015C", "bytes": 1, "formula": lambda a: a - 40},
    "INTAKE_PRESSURE":     {"pid": "010B", "bytes": 1, "formula": lambda a: a},
}


class OBDReader:
    """
    Reads vehicle data via OBD-II protocol.

    Automotive Background:
    ─────────────────────
    OBD-II (On-Board Diagnostics II) is a standardized system mandated in all
    cars sold in the US since 1996 (EU since 2001). It provides access to:

    - Real-time sensor data (Mode 01): RPM, speed, temperatures, fuel level
    - Freeze frame data (Mode 02): Snapshot when a fault occurred
    - Diagnostic Trouble Codes (Mode 03): Active fault codes (P0xxx, C0xxx, etc.)
    - Clear DTCs (Mode 04): Reset check engine light
    - Oxygen sensor data (Mode 05)
    - Vehicle info (Mode 09): VIN, calibration IDs

    Communication Protocols:
    - SAE J1850 PWM (Ford)
    - SAE J1850 VPW (GM)
    - ISO 9141-2 (Chrysler, Asian, European)
    - ISO 14230-4 KWP (Keyword Protocol)
    - ISO 15765-4 CAN (Modern vehicles, most common)
    """

    def __init__(self, port: str = "COM3", baudrate: int = 9600, timeout: float = 5.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.connection = None
        self.is_connected = False
        self._use_simulator = False

    def connect(self) -> bool:
        """
        Connect to the OBD-II adapter.
        Falls back to simulator mode if no adapter is found.
        """
        try:
            import obd
            self.connection = obd.OBD(self.port, baudrate=self.baudrate, timeout=self.timeout)
            if self.connection.is_connected():
                self.is_connected = True
                logger.info(f"Connected to OBD-II adapter on {self.port}")
                logger.info(f"Protocol: {self.connection.protocol_name()}")
                return True
            else:
                logger.warning("OBD-II adapter found but no vehicle connection")
                self._use_simulator = True
                return False
        except (ImportError, Exception) as e:
            logger.warning(f"OBD-II connection failed: {e}. Using simulator mode.")
            self._use_simulator = True
            return False

    def read_all_sensors(self) -> Dict[str, Any]:
        """
        Read all available OBD-II sensor values.

        Returns a dictionary with sensor names and their current values.
        """
        if self._use_simulator:
            return self._simulate_sensor_data()

        data = {}
        try:
            import obd
            cmd_map = {
                "engine_rpm": obd.commands.RPM,
                "vehicle_speed": obd.commands.SPEED,
                "coolant_temp": obd.commands.COOLANT_TEMP,
                "engine_load": obd.commands.ENGINE_LOAD,
                "throttle_position": obd.commands.THROTTLE_POS,
                "intake_air_temp": obd.commands.INTAKE_TEMP,
                "mass_air_flow": obd.commands.MAF,
                "fuel_level": obd.commands.FUEL_LEVEL,
                "battery_voltage": obd.commands.CONTROL_MODULE_VOLTAGE,
                "intake_manifold_pressure": obd.commands.INTAKE_PRESSURE,
            }

            for name, cmd in cmd_map.items():
                try:
                    response = self.connection.query(cmd)
                    if not response.is_null():
                        data[name] = response.value.magnitude if hasattr(response.value, 'magnitude') else response.value
                    else:
                        data[name] = None
                except Exception:
                    data[name] = None

        except Exception as e:
            logger.error(f"Error reading OBD sensors: {e}")
            data = self._simulate_sensor_data()

        data["timestamp"] = datetime.utcnow().isoformat()
        return data

    def read_dtcs(self) -> List[Dict[str, str]]:
        """
        Read Diagnostic Trouble Codes from the vehicle ECU.

        DTC Format:
        ──────────
        - P0xxx: Powertrain (engine, transmission)
        - C0xxx: Chassis (ABS, steering)
        - B0xxx: Body (airbags, A/C)
        - U0xxx: Network (CAN bus communication)

        Example: P0301 = Cylinder 1 Misfire Detected
        """
        if self._use_simulator:
            return self._simulate_dtcs()

        dtcs = []
        try:
            import obd
            response = self.connection.query(obd.commands.GET_DTC)
            if not response.is_null():
                for code, description in response.value:
                    dtcs.append({"code": code, "description": description})
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")

        return dtcs

    def get_vehicle_info(self) -> Dict[str, str]:
        """Read Mode 09 vehicle information (VIN, etc.)."""
        if self._use_simulator:
            return {"vin": "SIM00000000000001", "protocol": "Simulated"}

        info = {}
        try:
            import obd
            vin_response = self.connection.query(obd.commands.VIN)
            if not vin_response.is_null():
                info["vin"] = str(vin_response.value)
            info["protocol"] = self.connection.protocol_name()
        except Exception as e:
            logger.error(f"Error reading vehicle info: {e}")

        return info

    def disconnect(self):
        """Close the OBD-II connection."""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("OBD-II connection closed")

    def _simulate_sensor_data(self) -> Dict[str, Any]:
        """Generate simulated sensor data for development/testing."""
        import random
        return {
            "engine_rpm": round(random.uniform(700, 4500), 1),
            "vehicle_speed": round(random.uniform(0, 130), 1),
            "coolant_temp": round(random.uniform(80, 105), 1),
            "engine_load": round(random.uniform(10, 85), 1),
            "throttle_position": round(random.uniform(5, 80), 1),
            "intake_air_temp": round(random.uniform(20, 50), 1),
            "mass_air_flow": round(random.uniform(2, 25), 2),
            "fuel_level": round(random.uniform(10, 95), 1),
            "battery_voltage": round(random.uniform(12.0, 14.5), 2),
            "intake_manifold_pressure": round(random.uniform(20, 100), 1),
            "engine_oil_temp": round(random.uniform(80, 120), 1),
            "fuel_consumption_rate": round(random.uniform(2, 15), 2),
        }

    def _simulate_dtcs(self) -> List[Dict[str, str]]:
        """Simulated DTCs for development."""
        import random
        sample_dtcs = [
            {"code": "P0301", "description": "Cylinder 1 Misfire Detected"},
            {"code": "P0420", "description": "Catalyst System Efficiency Below Threshold"},
            {"code": "P0171", "description": "System Too Lean (Bank 1)"},
            {"code": "P0128", "description": "Coolant Thermostat Below Operating Temperature"},
            {"code": "P0442", "description": "EVAP System Small Leak Detected"},
        ]
        count = random.randint(0, 2)
        return random.sample(sample_dtcs, min(count, len(sample_dtcs)))
