"""
Fleet Management System - Configuration Settings
Centralized configuration for all modules including telematics, database, and API.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    DB_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'fleet.db'}"
    ECHO_SQL: bool = False

    class Config:
        env_prefix = "DB_"


class TelematicsSettings(BaseSettings):
    """Telematics & vehicle communication settings."""

    # OBD-II Configuration
    OBD_PORT: str = "COM3"  # Serial port for OBD-II adapter (Windows)
    OBD_BAUDRATE: int = 9600
    OBD_TIMEOUT: float = 5.0
    OBD_PROTOCOL: str = "AUTO"  # AUTO, SAE_J1850_PWM, ISO_15765_4_CAN, etc.

    # CAN Bus Configuration
    CAN_INTERFACE: str = "socketcan"  # socketcan, pcan, vector, kvaser
    CAN_CHANNEL: str = "vcan0"
    CAN_BITRATE: int = 500000  # 500 kbps (standard automotive CAN)

    # GPS Configuration
    GPS_UPDATE_INTERVAL: float = 1.0  # seconds
    GPS_PORT: str = "COM4"
    GPS_BAUDRATE: int = 9600

    # MQTT Broker (for real-time telematics data)
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "fleet/vehicles"
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    # Data Collection
    TELEMETRY_INTERVAL: float = 2.0  # seconds between data polls
    DATA_RETENTION_DAYS: int = 90  # how long to keep telemetry data

    class Config:
        env_prefix = "TELEM_"


class AlertSettings(BaseSettings):
    """Alert thresholds for driver behavior and vehicle health."""

    # Speed thresholds (km/h)
    SPEED_LIMIT_WARNING: float = 120.0
    SPEED_LIMIT_CRITICAL: float = 150.0

    # Engine thresholds
    ENGINE_TEMP_WARNING: float = 100.0  # °C
    ENGINE_TEMP_CRITICAL: float = 115.0
    RPM_WARNING: int = 5500
    RPM_CRITICAL: int = 6500

    # Driver behavior
    HARSH_BRAKE_THRESHOLD: float = -8.0  # m/s² deceleration
    HARSH_ACCEL_THRESHOLD: float = 5.0  # m/s² acceleration
    IDLE_TIME_WARNING: int = 300  # seconds

    # Fuel
    FUEL_LOW_WARNING: float = 15.0  # percentage
    FUEL_LOW_CRITICAL: float = 5.0

    # Geofence
    GEOFENCE_RADIUS_DEFAULT: float = 5000.0  # meters

    # Maintenance
    MAINTENANCE_MILEAGE_INTERVAL: int = 10000  # km
    MAINTENANCE_TIME_INTERVAL: int = 180  # days

    class Config:
        env_prefix = "ALERT_"


class APISettings(BaseSettings):
    """API server settings."""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production-fleet-mgmt-2026"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_prefix = "API_"


class AppSettings:
    """Main application settings aggregator."""

    def __init__(self):
        self.db = DatabaseSettings()
        self.telematics = TelematicsSettings()
        self.alerts = AlertSettings()
        self.api = APISettings()
        self.base_dir = BASE_DIR

        # Ensure data directory exists
        (BASE_DIR / "data").mkdir(exist_ok=True)


# Global settings instance
settings = AppSettings()
