"""
CAN Bus Decoder — Reads and decodes CAN 2.0 / CAN-FD frames.

This module interfaces with the vehicle's Controller Area Network (CAN bus),
the primary communication backbone in modern automobiles.

Automotive CAN Bus Overview:
────────────────────────────
CAN (Controller Area Network) is a robust serial bus standard (ISO 11898)
developed by Bosch. Modern cars have 2-5 CAN buses:

1. Powertrain CAN (500 kbps) — Engine ECU, Transmission, ABS
2. Body CAN (125-250 kbps) — Lights, windows, locks, climate
3. Infotainment CAN — Head unit, Bluetooth, navigation
4. Chassis CAN — Suspension, steering, stability control
5. ADAS CAN — Cameras, radar, lidar (newer vehicles)

CAN Frame Structure (Standard 2.0A):
┌─────┬────────┬─────┬────┬──────────────┬─────┬─────┬─────┐
│ SOF │ 11-bit │ RTR │ DLC│ Data (0-8B)  │ CRC │ ACK │ EOF │
│     │  Arb ID│     │    │              │     │     │     │
└─────┴────────┴─────┴────┴──────────────┴─────┴─────┴─────┘
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


# Common automotive CAN IDs and their signals (generic, varies by manufacturer)
STANDARD_CAN_SIGNALS = {
    0x0C0: {
        "name": "Engine_Data_1",
        "signals": {
            "engine_rpm":     {"start_bit": 0,  "length": 16, "factor": 0.25, "offset": 0, "unit": "rpm"},
            "engine_torque":  {"start_bit": 16, "length": 16, "factor": 0.1,  "offset": -500, "unit": "Nm"},
        }
    },
    0x0C1: {
        "name": "Engine_Data_2",
        "signals": {
            "coolant_temp":   {"start_bit": 0,  "length": 8, "factor": 1, "offset": -40, "unit": "°C"},
            "oil_pressure":   {"start_bit": 8,  "length": 8, "factor": 4, "offset": 0, "unit": "kPa"},
            "oil_temp":       {"start_bit": 16, "length": 8, "factor": 1, "offset": -40, "unit": "°C"},
        }
    },
    0x0D0: {
        "name": "Vehicle_Speed",
        "signals": {
            "vehicle_speed":  {"start_bit": 0, "length": 16, "factor": 0.01, "offset": 0, "unit": "km/h"},
            "wheel_speed_fl": {"start_bit": 16, "length": 16, "factor": 0.01, "offset": 0, "unit": "km/h"},
            "wheel_speed_fr": {"start_bit": 32, "length": 16, "factor": 0.01, "offset": 0, "unit": "km/h"},
        }
    },
    0x0D1: {
        "name": "Brake_Data",
        "signals": {
            "brake_pressure": {"start_bit": 0,  "length": 16, "factor": 0.1, "offset": 0, "unit": "bar"},
            "brake_pedal":    {"start_bit": 16, "length": 8,  "factor": 0.4, "offset": 0, "unit": "%"},
            "abs_active":     {"start_bit": 24, "length": 1,  "factor": 1,   "offset": 0, "unit": "bool"},
        }
    },
    0x0E0: {
        "name": "Transmission_Data",
        "signals": {
            "gear_position":  {"start_bit": 0,  "length": 4, "factor": 1, "offset": 0, "unit": ""},
            "trans_temp":     {"start_bit": 8,  "length": 8, "factor": 1, "offset": -40, "unit": "°C"},
        }
    },
    0x3B0: {
        "name": "Fuel_Data",
        "signals": {
            "fuel_level":     {"start_bit": 0,  "length": 8,  "factor": 0.5, "offset": 0, "unit": "%"},
            "fuel_rate":      {"start_bit": 8,  "length": 16, "factor": 0.05, "offset": 0, "unit": "L/h"},
        }
    },
    0x3C0: {
        "name": "Battery_Data",
        "signals": {
            "battery_voltage": {"start_bit": 0, "length": 16, "factor": 0.001, "offset": 0, "unit": "V"},
            "alternator_load": {"start_bit": 16, "length": 8,  "factor": 1,     "offset": 0, "unit": "%"},
        }
    },
}


class CANDecoder:
    """
    Decodes raw CAN bus frames into human-readable vehicle data.

    This class processes raw CAN frames using a DBC-like signal database.
    In production, you'd use a real .dbc file from the vehicle manufacturer.
    """

    def __init__(self, signal_db: Optional[Dict] = None):
        self.signal_db = signal_db or STANDARD_CAN_SIGNALS
        self.bus = None
        self.is_connected = False
        self._use_simulator = False
        self._listeners: List[Callable] = []

    def connect(self, interface: str = "socketcan", channel: str = "vcan0", bitrate: int = 500000) -> bool:
        """
        Connect to a CAN bus interface.

        Supported interfaces:
        - socketcan: Linux SocketCAN (vcan0 for virtual, can0 for hardware)
        - pcan: PEAK-System PCAN-USB adapter
        - vector: Vector CANalyzer/CANoe
        - kvaser: Kvaser CAN interface
        """
        try:
            import can
            self.bus = can.interface.Bus(channel=channel, interface=interface, bitrate=bitrate)
            self.is_connected = True
            logger.info(f"CAN bus connected: {interface}:{channel} @ {bitrate} bps")
            return True
        except Exception as e:
            logger.warning(f"CAN bus connection failed: {e}. Using simulator.")
            self._use_simulator = True
            return False

    def decode_frame(self, arbitration_id: int, data: bytes) -> Dict[str, Any]:
        """
        Decode a single CAN frame into signal values.

        Parameters:
            arbitration_id: CAN arbitration ID (11-bit or 29-bit)
            data: Raw data bytes (up to 8 bytes for CAN 2.0, 64 for CAN-FD)

        Returns:
            Dictionary of decoded signal names and values.
        """
        result = {}

        if arbitration_id in self.signal_db:
            frame_def = self.signal_db[arbitration_id]
            result["_frame_name"] = frame_def["name"]

            for signal_name, signal_def in frame_def["signals"].items():
                try:
                    raw_value = self._extract_signal(
                        data,
                        signal_def["start_bit"],
                        signal_def["length"]
                    )
                    physical_value = raw_value * signal_def["factor"] + signal_def["offset"]
                    result[signal_name] = {
                        "value": round(physical_value, 3),
                        "unit": signal_def["unit"],
                        "raw": raw_value,
                    }
                except Exception as e:
                    logger.debug(f"Could not decode signal {signal_name}: {e}")

        return result

    @staticmethod
    def _extract_signal(data: bytes, start_bit: int, length: int) -> int:
        """
        Extract a signal from CAN data bytes using bit-level addressing.
        Uses Intel (little-endian) byte order (most common in automotive CAN).
        """
        value = int.from_bytes(data, byteorder="little")
        mask = (1 << length) - 1
        return (value >> start_bit) & mask

    def read_frame(self) -> Optional[Dict]:
        """Read and decode a single CAN frame."""
        if self._use_simulator:
            return self._simulate_frame()

        try:
            msg = self.bus.recv(timeout=1.0)
            if msg:
                decoded = self.decode_frame(msg.arbitration_id, msg.data)
                decoded["_arbitration_id"] = hex(msg.arbitration_id)
                decoded["_timestamp"] = msg.timestamp
                decoded["_raw_data"] = msg.data.hex()
                return decoded
        except Exception as e:
            logger.error(f"CAN read error: {e}")
        return None

    def read_all_signals(self) -> Dict[str, Any]:
        """Read multiple CAN frames and aggregate all decoded signals."""
        if self._use_simulator:
            return self._simulate_all_signals()

        all_signals = {}
        for _ in range(50):  # Read up to 50 frames
            frame = self.read_frame()
            if frame:
                for key, val in frame.items():
                    if not key.startswith("_"):
                        all_signals[key] = val
        return all_signals

    def disconnect(self):
        """Shutdown the CAN bus connection."""
        if self.bus:
            self.bus.shutdown()
            self.is_connected = False
            logger.info("CAN bus disconnected")

    def _simulate_frame(self) -> Dict:
        """Simulate a CAN frame for development."""
        import random
        arb_id = random.choice(list(self.signal_db.keys()))
        frame_def = self.signal_db[arb_id]
        result = {"_frame_name": frame_def["name"], "_arbitration_id": hex(arb_id)}

        for signal_name, signal_def in frame_def["signals"].items():
            max_raw = (1 << signal_def["length"]) - 1
            raw_value = random.randint(0, max_raw)
            physical_value = raw_value * signal_def["factor"] + signal_def["offset"]
            result[signal_name] = {
                "value": round(physical_value, 3),
                "unit": signal_def["unit"],
                "raw": raw_value,
            }

        return result

    def _simulate_all_signals(self) -> Dict[str, Any]:
        """Simulate aggregated signal data."""
        import random
        return {
            "engine_rpm": {"value": round(random.uniform(700, 4500), 1), "unit": "rpm"},
            "vehicle_speed": {"value": round(random.uniform(0, 130), 1), "unit": "km/h"},
            "coolant_temp": {"value": round(random.uniform(80, 105), 1), "unit": "°C"},
            "brake_pressure": {"value": round(random.uniform(0, 80), 1), "unit": "bar"},
            "fuel_level": {"value": round(random.uniform(10, 95), 1), "unit": "%"},
            "battery_voltage": {"value": round(random.uniform(12.0, 14.5), 2), "unit": "V"},
            "gear_position": {"value": random.randint(0, 6), "unit": ""},
        }
