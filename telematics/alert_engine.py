"""
Alert Engine — Real-time monitoring and alert generation.

Processes incoming telemetry data against configurable thresholds
to generate alerts for fleet managers.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.settings import settings
from models.alert import AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Evaluates telemetry data against thresholds and generates alerts.

    Alert Categories:
    ─────────────────
    1. Speed Monitoring: Speeding warnings/violations
    2. Engine Health: Overheating, over-revving, oil pressure
    3. Fuel Monitoring: Low fuel warnings
    4. Driver Behavior: Harsh braking, acceleration, cornering
    5. Geofence: Entry/exit from defined zones
    6. Maintenance: Predictive maintenance alerts
    7. Device Health: Telematics device offline/malfunction
    """

    def __init__(self):
        self.thresholds = settings.alerts
        self._alert_cooldowns: Dict[str, datetime] = {}  # Prevent alert spam
        self.cooldown_seconds = 300  # 5 min between same alerts

    def evaluate(self, vehicle_id: int, telemetry: Dict[str, Any]) -> List[Dict]:
        """
        Evaluate telemetry data and generate alerts.

        Parameters:
            vehicle_id: ID of the vehicle
            telemetry: Current telemetry data dictionary

        Returns:
            List of alert dictionaries to be created
        """
        alerts = []

        # Speed checks
        speed = telemetry.get("vehicle_speed") or telemetry.get("gps_speed") or 0
        alerts.extend(self._check_speed(vehicle_id, speed, telemetry))

        # Engine temperature
        coolant_temp = telemetry.get("coolant_temp")
        if coolant_temp is not None:
            alerts.extend(self._check_engine_temp(vehicle_id, coolant_temp, telemetry))

        # Engine RPM
        rpm = telemetry.get("engine_rpm")
        if rpm is not None:
            alerts.extend(self._check_rpm(vehicle_id, rpm, telemetry))

        # Fuel level
        fuel = telemetry.get("fuel_level")
        if fuel is not None:
            alerts.extend(self._check_fuel(vehicle_id, fuel, telemetry))

        # Battery voltage
        voltage = telemetry.get("battery_voltage")
        if voltage is not None:
            alerts.extend(self._check_battery(vehicle_id, voltage, telemetry))

        # Driver behavior (acceleration-based)
        accel_y = telemetry.get("acceleration_y")
        if accel_y is not None:
            alerts.extend(self._check_driver_behavior(vehicle_id, telemetry))

        # DTC codes
        dtcs = telemetry.get("dtc_codes")
        if dtcs:
            alerts.extend(self._check_dtcs(vehicle_id, dtcs, telemetry))

        return alerts

    def check_geofence(self, vehicle_id: int, lat: float, lon: float, geofences: list) -> List[Dict]:
        """Check if vehicle is inside/outside defined geofences."""
        from telematics.gps_tracker import GPSTracker

        alerts = []
        for fence in geofences:
            inside = GPSTracker.is_inside_geofence(
                lat, lon, fence.center_latitude, fence.center_longitude, fence.radius_meters
            )

            if not inside and fence.alert_on_exit:
                alert = self._create_alert(
                    vehicle_id=vehicle_id,
                    alert_type=AlertType.GEOFENCE_VIOLATION,
                    severity=AlertSeverity.WARNING,
                    message=f"Vehicle exited geofence: {fence.name}",
                    lat=lat, lon=lon,
                    trigger_value=0, threshold_value=fence.radius_meters,
                )
                if alert:
                    alerts.append(alert)

            if inside and fence.alert_on_entry:
                alert = self._create_alert(
                    vehicle_id=vehicle_id,
                    alert_type=AlertType.GEOFENCE_VIOLATION,
                    severity=AlertSeverity.INFO,
                    message=f"Vehicle entered geofence: {fence.name}",
                    lat=lat, lon=lon,
                )
                if alert:
                    alerts.append(alert)

        return alerts

    def _check_speed(self, vehicle_id: int, speed: float, telemetry: Dict) -> List[Dict]:
        alerts = []
        if speed >= self.thresholds.SPEED_LIMIT_CRITICAL:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.SPEEDING,
                severity=AlertSeverity.CRITICAL,
                message=f"CRITICAL SPEEDING: {speed:.0f} km/h (limit: {self.thresholds.SPEED_LIMIT_CRITICAL})",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=speed, threshold_value=self.thresholds.SPEED_LIMIT_CRITICAL,
            )
            if alert:
                alerts.append(alert)
        elif speed >= self.thresholds.SPEED_LIMIT_WARNING:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.SPEEDING,
                severity=AlertSeverity.WARNING,
                message=f"Speed warning: {speed:.0f} km/h (limit: {self.thresholds.SPEED_LIMIT_WARNING})",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=speed, threshold_value=self.thresholds.SPEED_LIMIT_WARNING,
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _check_engine_temp(self, vehicle_id: int, temp: float, telemetry: Dict) -> List[Dict]:
        alerts = []
        if temp >= self.thresholds.ENGINE_TEMP_CRITICAL:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.ENGINE_OVERHEAT,
                severity=AlertSeverity.CRITICAL,
                message=f"ENGINE OVERHEAT: {temp:.1f}°C (limit: {self.thresholds.ENGINE_TEMP_CRITICAL}°C)",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=temp, threshold_value=self.thresholds.ENGINE_TEMP_CRITICAL,
            )
            if alert:
                alerts.append(alert)
        elif temp >= self.thresholds.ENGINE_TEMP_WARNING:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.ENGINE_OVERHEAT,
                severity=AlertSeverity.WARNING,
                message=f"Engine temp high: {temp:.1f}°C (warning: {self.thresholds.ENGINE_TEMP_WARNING}°C)",
                trigger_value=temp, threshold_value=self.thresholds.ENGINE_TEMP_WARNING,
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _check_rpm(self, vehicle_id: int, rpm: float, telemetry: Dict) -> List[Dict]:
        alerts = []
        if rpm >= self.thresholds.RPM_CRITICAL:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.ENGINE_OVERHEAT,
                severity=AlertSeverity.CRITICAL,
                message=f"Engine over-revving: {rpm:.0f} RPM (limit: {self.thresholds.RPM_CRITICAL})",
                trigger_value=rpm, threshold_value=self.thresholds.RPM_CRITICAL,
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _check_fuel(self, vehicle_id: int, fuel: float, telemetry: Dict) -> List[Dict]:
        alerts = []
        if fuel <= self.thresholds.FUEL_LOW_CRITICAL:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.LOW_FUEL,
                severity=AlertSeverity.CRITICAL,
                message=f"FUEL CRITICAL: {fuel:.1f}% remaining",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=fuel, threshold_value=self.thresholds.FUEL_LOW_CRITICAL,
            )
            if alert:
                alerts.append(alert)
        elif fuel <= self.thresholds.FUEL_LOW_WARNING:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.LOW_FUEL,
                severity=AlertSeverity.WARNING,
                message=f"Low fuel warning: {fuel:.1f}% remaining",
                trigger_value=fuel, threshold_value=self.thresholds.FUEL_LOW_WARNING,
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _check_battery(self, vehicle_id: int, voltage: float, telemetry: Dict) -> List[Dict]:
        alerts = []
        if voltage < 11.5:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.LOW_BATTERY,
                severity=AlertSeverity.WARNING,
                message=f"Low battery voltage: {voltage:.2f}V",
                trigger_value=voltage, threshold_value=11.5,
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _check_driver_behavior(self, vehicle_id: int, telemetry: Dict) -> List[Dict]:
        alerts = []
        accel_y = telemetry.get("acceleration_y", 0)

        if accel_y <= self.thresholds.HARSH_BRAKE_THRESHOLD:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.HARSH_BRAKING,
                severity=AlertSeverity.WARNING,
                message=f"Harsh braking detected: {accel_y:.1f} m/s²",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=accel_y, threshold_value=self.thresholds.HARSH_BRAKE_THRESHOLD,
            )
            if alert:
                alerts.append(alert)

        if accel_y >= self.thresholds.HARSH_ACCEL_THRESHOLD:
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.HARSH_ACCELERATION,
                severity=AlertSeverity.WARNING,
                message=f"Harsh acceleration detected: {accel_y:.1f} m/s²",
                lat=telemetry.get("latitude"), lon=telemetry.get("longitude"),
                trigger_value=accel_y, threshold_value=self.thresholds.HARSH_ACCEL_THRESHOLD,
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _check_dtcs(self, vehicle_id: int, dtcs: list, telemetry: Dict) -> List[Dict]:
        alerts = []
        for dtc in dtcs[:5]:  # Limit to first 5 DTCs
            code = dtc if isinstance(dtc, str) else dtc.get("code", "")
            alert = self._create_alert(
                vehicle_id=vehicle_id,
                alert_type=AlertType.DTC_DETECTED,
                severity=AlertSeverity.WARNING,
                message=f"DTC Detected: {code}",
                details=str(dtc),
            )
            if alert:
                alerts.append(alert)
        return alerts

    def _create_alert(self, vehicle_id: int, alert_type: AlertType,
                      severity: AlertSeverity, message: str,
                      lat=None, lon=None, trigger_value=None,
                      threshold_value=None, details=None) -> Optional[Dict]:
        """Create an alert dict if not in cooldown period."""
        cooldown_key = f"{vehicle_id}_{alert_type.value}_{severity.value}"
        now = datetime.utcnow()

        # Check cooldown
        if cooldown_key in self._alert_cooldowns:
            elapsed = (now - self._alert_cooldowns[cooldown_key]).total_seconds()
            if elapsed < self.cooldown_seconds:
                return None

        self._alert_cooldowns[cooldown_key] = now

        return {
            "vehicle_id": vehicle_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "details": details,
            "latitude": lat,
            "longitude": lon,
            "trigger_value": trigger_value,
            "threshold_value": threshold_value,
            "created_at": now,
        }
