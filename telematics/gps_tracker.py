"""
GPS Tracker — Handles vehicle geolocation via GPS/GNSS module.

Supports NMEA 0183 protocol used by most automotive GPS receivers.
Falls back to simulation mode for development.
"""

import logging
import math
from typing import Optional, Dict, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


class GPSTracker:
    """
    Vehicle GPS tracking module.

    Automotive GPS Context:
    ──────────────────────
    Fleet vehicles typically use dedicated GPS/GNSS receivers that output
    NMEA 0183 sentences (GGA, RMC, VTG) over serial/UART.

    Common NMEA sentences:
    - $GPGGA: Position fix (lat, lon, altitude, satellite count)
    - $GPRMC: Recommended minimum (lat, lon, speed, course, date)
    - $GPVTG: Course and speed over ground

    Modern telematics use multi-constellation: GPS + GLONASS + Galileo + BeiDou
    for better accuracy (sub-meter with RTK).
    """

    def __init__(self, port: str = "COM4", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self._use_simulator = False

        # Track history for speed/heading calculation
        self._last_position = None
        self._last_time = None

    def connect(self) -> bool:
        """Connect to the GPS serial device."""
        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2)
            self.is_connected = True
            logger.info(f"GPS connected on {self.port}")
            return True
        except Exception as e:
            logger.warning(f"GPS connection failed: {e}. Using simulator.")
            self._use_simulator = True
            return False

    def get_position(self) -> Dict:
        """
        Get current GPS position.

        Returns dict with: latitude, longitude, altitude, speed, heading, satellites
        """
        if self._use_simulator:
            return self._simulate_position()

        try:
            raw_data = self._read_nmea()
            return self._parse_nmea(raw_data)
        except Exception as e:
            logger.error(f"GPS read error: {e}")
            return self._simulate_position()

    def _read_nmea(self) -> List[str]:
        """Read NMEA sentences from serial port."""
        sentences = []
        try:
            for _ in range(20):  # Read up to 20 lines
                line = self.serial_conn.readline().decode("ascii", errors="ignore").strip()
                if line.startswith("$GP") or line.startswith("$GN"):
                    sentences.append(line)
        except Exception as e:
            logger.error(f"NMEA read error: {e}")
        return sentences

    def _parse_nmea(self, sentences: List[str]) -> Dict:
        """
        Parse NMEA 0183 sentences into structured data.

        Example $GPRMC sentence:
        $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A

        Fields: time, status, lat, N/S, lon, E/W, speed(knots), course, date, var, var_dir
        """
        data = {
            "latitude": None, "longitude": None, "altitude": None,
            "speed": None, "heading": None, "satellites": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for sentence in sentences:
            try:
                parts = sentence.split(",")

                if "GGA" in parts[0] and len(parts) >= 10:
                    data["latitude"] = self._nmea_to_decimal(parts[2], parts[3])
                    data["longitude"] = self._nmea_to_decimal(parts[4], parts[5])
                    data["altitude"] = float(parts[9]) if parts[9] else None
                    data["satellites"] = int(parts[7]) if parts[7] else None

                elif "RMC" in parts[0] and len(parts) >= 8:
                    if data["latitude"] is None:
                        data["latitude"] = self._nmea_to_decimal(parts[3], parts[4])
                        data["longitude"] = self._nmea_to_decimal(parts[5], parts[6])
                    speed_knots = float(parts[7]) if parts[7] else 0
                    data["speed"] = round(speed_knots * 1.852, 1)  # knots to km/h
                    data["heading"] = float(parts[8]) if parts[8] else None

            except (ValueError, IndexError):
                continue

        return data

    @staticmethod
    def _nmea_to_decimal(value: str, direction: str) -> Optional[float]:
        """Convert NMEA coordinate (DDMM.MMMM) to decimal degrees."""
        if not value or not direction:
            return None
        try:
            if "." in value:
                dot_index = value.index(".")
                degrees = float(value[:dot_index - 2])
                minutes = float(value[dot_index - 2:])
                decimal = degrees + minutes / 60.0
                if direction in ("S", "W"):
                    decimal = -decimal
                return round(decimal, 6)
        except (ValueError, IndexError):
            return None
        return None

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates in meters.
        Uses the Haversine formula (accurate for automotive distances).
        """
        R = 6371000  # Earth's radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    def is_inside_geofence(lat: float, lon: float, fence_lat: float, fence_lon: float, radius_m: float) -> bool:
        """Check if a GPS coordinate is within a circular geofence."""
        distance = GPSTracker.haversine_distance(lat, lon, fence_lat, fence_lon)
        return distance <= radius_m

    def _simulate_position(self) -> Dict:
        """Simulate GPS position for development (around New Delhi, India)."""
        import random
        base_lat, base_lon = 28.6139, 77.2090  # New Delhi
        return {
            "latitude": round(base_lat + random.uniform(-0.05, 0.05), 6),
            "longitude": round(base_lon + random.uniform(-0.05, 0.05), 6),
            "altitude": round(random.uniform(200, 250), 1),
            "speed": round(random.uniform(0, 80), 1),
            "heading": round(random.uniform(0, 360), 1),
            "satellites": random.randint(6, 14),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def disconnect(self):
        """Close GPS serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            logger.info("GPS connection closed")
