"""
Vehicle Tracking Service — Orchestrates real-time vehicle data collection.

This is the core service that:
1. Polls OBD-II data from the vehicle's ECU
2. Reads GPS position
3. Optionally reads CAN bus data
4. Passes everything through the alert engine
5. Stores telemetry in the database
"""

import logging
import time
import threading
from typing import Dict, Optional
from datetime import datetime

from models.database import SessionLocal
from models.vehicle import Vehicle, VehicleStatus
from models.telemetry import TelemetryData
from models.alert import Alert
from telematics.obd_reader import OBDReader
from telematics.gps_tracker import GPSTracker
from telematics.can_decoder import CANDecoder
from telematics.alert_engine import AlertEngine
from config.settings import settings

logger = logging.getLogger(__name__)


class VehicleTracker:
    """
    Real-time vehicle tracking and data collection service.

    Data Flow:
    ──────────
    Vehicle ECU ──► OBD-II Reader ──┐
    GPS Module  ──► GPS Tracker  ──┤──► Telemetry Processor ──► Database
    CAN Bus     ──► CAN Decoder  ──┘         │
                                              ▼
                                        Alert Engine ──► Alert Database
    """

    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
        self.obd = OBDReader(
            port=settings.telematics.OBD_PORT,
            baudrate=settings.telematics.OBD_BAUDRATE,
            timeout=settings.telematics.OBD_TIMEOUT,
        )
        self.gps = GPSTracker(
            port=settings.telematics.GPS_PORT,
            baudrate=settings.telematics.GPS_BAUDRATE,
        )
        self.can = CANDecoder()
        self.alert_engine = AlertEngine()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_interval = settings.telematics.TELEMETRY_INTERVAL

    def start(self):
        """Start the tracking loop in a background thread."""
        if self.is_running:
            logger.warning(f"Tracker for vehicle {self.vehicle_id} already running")
            return

        logger.info(f"Starting tracker for vehicle {self.vehicle_id}")
        self.obd.connect()
        self.gps.connect()
        self.can.connect()

        self.is_running = True
        self._thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tracking loop."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=10)
        self.obd.disconnect()
        self.gps.disconnect()
        self.can.disconnect()
        logger.info(f"Tracker for vehicle {self.vehicle_id} stopped")

    def _tracking_loop(self):
        """Main loop: poll sensors, process data, store to DB."""
        while self.is_running:
            try:
                telemetry = self.collect_telemetry()
                self._store_telemetry(telemetry)
                time.sleep(self._poll_interval)
            except Exception as e:
                logger.error(f"Tracking error for vehicle {self.vehicle_id}: {e}")
                time.sleep(5)  # Back off on error

    def collect_telemetry(self) -> Dict:
        """Collect data from all telematics sources."""
        # 1. Read OBD-II sensor data
        obd_data = self.obd.read_all_sensors()

        # 2. Read GPS position
        gps_data = self.gps.get_position()

        # 3. Read CAN bus signals (optional)
        can_data = self.can.read_all_signals()

        # 4. Read DTCs
        dtc_data = self.obd.read_dtcs()

        # 5. Merge all data into one telemetry record
        telemetry = {
            "vehicle_id": self.vehicle_id,
            "timestamp": datetime.utcnow(),

            # GPS
            "latitude": gps_data.get("latitude"),
            "longitude": gps_data.get("longitude"),
            "altitude": gps_data.get("altitude"),
            "heading": gps_data.get("heading"),
            "gps_speed": gps_data.get("speed"),
            "satellites": gps_data.get("satellites"),

            # OBD-II
            "engine_rpm": obd_data.get("engine_rpm"),
            "vehicle_speed": obd_data.get("vehicle_speed"),
            "throttle_position": obd_data.get("throttle_position"),
            "engine_load": obd_data.get("engine_load"),
            "coolant_temp": obd_data.get("coolant_temp"),
            "intake_air_temp": obd_data.get("intake_air_temp"),
            "mass_air_flow": obd_data.get("mass_air_flow"),
            "fuel_level": obd_data.get("fuel_level"),
            "fuel_consumption_rate": obd_data.get("fuel_consumption_rate"),
            "battery_voltage": obd_data.get("battery_voltage"),
            "engine_oil_temp": obd_data.get("engine_oil_temp"),

            # DTCs
            "dtc_codes": [d["code"] for d in dtc_data] if dtc_data else None,

            # CAN (extract values from CAN signal dicts)
            "raw_can_data": {k: v for k, v in can_data.items() if isinstance(v, dict)},
        }

        return telemetry

    def _store_telemetry(self, telemetry: Dict):
        """Store telemetry record and evaluate alerts."""
        db = SessionLocal()
        try:
            # Create telemetry record
            record = TelemetryData(
                vehicle_id=telemetry["vehicle_id"],
                timestamp=telemetry["timestamp"],
                latitude=telemetry.get("latitude"),
                longitude=telemetry.get("longitude"),
                altitude=telemetry.get("altitude"),
                heading=telemetry.get("heading"),
                gps_speed=telemetry.get("gps_speed"),
                satellites=telemetry.get("satellites"),
                engine_rpm=telemetry.get("engine_rpm"),
                vehicle_speed=telemetry.get("vehicle_speed"),
                throttle_position=telemetry.get("throttle_position"),
                engine_load=telemetry.get("engine_load"),
                coolant_temp=telemetry.get("coolant_temp"),
                intake_air_temp=telemetry.get("intake_air_temp"),
                mass_air_flow=telemetry.get("mass_air_flow"),
                fuel_level=telemetry.get("fuel_level"),
                fuel_consumption_rate=telemetry.get("fuel_consumption_rate"),
                battery_voltage=telemetry.get("battery_voltage"),
                engine_oil_temp=telemetry.get("engine_oil_temp"),
                dtc_codes=telemetry.get("dtc_codes"),
                raw_can_data=telemetry.get("raw_can_data"),
            )
            db.add(record)

            # Update vehicle state
            vehicle = db.query(Vehicle).filter(Vehicle.id == self.vehicle_id).first()
            if vehicle:
                if telemetry.get("latitude"):
                    vehicle.current_latitude = telemetry["latitude"]
                    vehicle.current_longitude = telemetry["longitude"]
                speed = telemetry.get("vehicle_speed") or telemetry.get("gps_speed") or 0
                vehicle.current_speed = speed
                if telemetry.get("fuel_level"):
                    vehicle.current_fuel_level = telemetry["fuel_level"]
                vehicle.last_telemetry_at = telemetry["timestamp"]

                # Update status based on speed
                if speed > 5:
                    vehicle.status = VehicleStatus.IN_TRANSIT
                else:
                    vehicle.status = VehicleStatus.IDLE

            # Evaluate alerts
            alerts = self.alert_engine.evaluate(self.vehicle_id, telemetry)
            for alert_data in alerts:
                alert = Alert(
                    vehicle_id=alert_data["vehicle_id"],
                    alert_type=alert_data["alert_type"],
                    severity=alert_data["severity"],
                    message=alert_data["message"],
                    details=alert_data.get("details"),
                    latitude=alert_data.get("latitude"),
                    longitude=alert_data.get("longitude"),
                    trigger_value=alert_data.get("trigger_value"),
                    threshold_value=alert_data.get("threshold_value"),
                )
                db.add(alert)

            db.commit()
            logger.debug(f"Stored telemetry for vehicle {self.vehicle_id}: speed={speed}, fuel={telemetry.get('fuel_level')}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store telemetry: {e}")
        finally:
            db.close()

    def get_single_reading(self) -> Dict:
        """Get a single telemetry snapshot (for API calls)."""
        return self.collect_telemetry()


class FleetTrackingService:
    """
    Manages tracking for all vehicles in the fleet.
    """

    def __init__(self):
        self.trackers: Dict[int, VehicleTracker] = {}

    def start_tracking(self, vehicle_id: int):
        """Start tracking a specific vehicle."""
        if vehicle_id not in self.trackers:
            tracker = VehicleTracker(vehicle_id)
            tracker.start()
            self.trackers[vehicle_id] = tracker
            logger.info(f"Started tracking vehicle {vehicle_id}")

    def stop_tracking(self, vehicle_id: int):
        """Stop tracking a specific vehicle."""
        if vehicle_id in self.trackers:
            self.trackers[vehicle_id].stop()
            del self.trackers[vehicle_id]
            logger.info(f"Stopped tracking vehicle {vehicle_id}")

    def start_all(self):
        """Start tracking all active vehicles in the database."""
        db = SessionLocal()
        try:
            vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
            for vehicle in vehicles:
                self.start_tracking(vehicle.id)
            logger.info(f"Started tracking {len(vehicles)} vehicles")
        finally:
            db.close()

    def stop_all(self):
        """Stop all active trackers."""
        for vid in list(self.trackers.keys()):
            self.stop_tracking(vid)

    def get_status(self) -> Dict:
        """Get tracking status for all vehicles."""
        return {
            "active_trackers": len(self.trackers),
            "vehicles": {vid: {"running": t.is_running} for vid, t in self.trackers.items()},
        }
