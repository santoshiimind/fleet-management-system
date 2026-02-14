"""
Telemetry data model — stores time-series vehicle telemetry readings.
Each record is a snapshot from the vehicle's OBD-II / CAN bus / GPS.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base


class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # ── GPS Data ──────────────────────────────────────────────
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)           # meters
    heading = Column(Float, nullable=True)             # degrees (0-360)
    gps_speed = Column(Float, nullable=True)           # km/h from GPS
    satellites = Column(Integer, nullable=True)

    # ── OBD-II Engine Data ────────────────────────────────────
    engine_rpm = Column(Float, nullable=True)
    vehicle_speed = Column(Float, nullable=True)       # km/h from ECU
    throttle_position = Column(Float, nullable=True)   # percentage
    engine_load = Column(Float, nullable=True)         # percentage
    coolant_temp = Column(Float, nullable=True)        # °C
    intake_air_temp = Column(Float, nullable=True)     # °C
    intake_manifold_pressure = Column(Float, nullable=True)  # kPa
    mass_air_flow = Column(Float, nullable=True)       # g/s
    fuel_level = Column(Float, nullable=True)          # percentage
    fuel_pressure = Column(Float, nullable=True)       # kPa
    fuel_consumption_rate = Column(Float, nullable=True)  # L/h
    engine_oil_temp = Column(Float, nullable=True)     # °C
    battery_voltage = Column(Float, nullable=True)     # V

    # ── Diagnostic Trouble Codes (DTCs) ───────────────────────
    dtc_codes = Column(JSON, nullable=True)            # List of active DTC strings

    # ── Accelerometer / IMU Data ──────────────────────────────
    acceleration_x = Column(Float, nullable=True)      # m/s² (lateral)
    acceleration_y = Column(Float, nullable=True)      # m/s² (longitudinal)
    acceleration_z = Column(Float, nullable=True)      # m/s² (vertical)

    # ── Driver Behavior Metrics ───────────────────────────────
    harsh_braking = Column(Float, default=0)           # flag/intensity
    harsh_acceleration = Column(Float, default=0)
    sharp_cornering = Column(Float, default=0)

    # ── Odometer & Trip ───────────────────────────────────────
    odometer = Column(Float, nullable=True)            # km
    trip_distance = Column(Float, nullable=True)       # km since trip start

    # ── Raw CAN Bus Data ──────────────────────────────────────
    raw_can_data = Column(JSON, nullable=True)         # Raw CAN frame payloads

    # Relationships
    vehicle = relationship("Vehicle", back_populates="telemetry_data")

    def __repr__(self):
        return f"<Telemetry vehicle={self.vehicle_id} t={self.timestamp}>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": {"lat": self.latitude, "lng": self.longitude, "alt": self.altitude},
            "speed": self.vehicle_speed or self.gps_speed,
            "engine": {
                "rpm": self.engine_rpm,
                "load": self.engine_load,
                "coolant_temp": self.coolant_temp,
                "throttle": self.throttle_position,
                "oil_temp": self.engine_oil_temp,
            },
            "fuel": {
                "level": self.fuel_level,
                "consumption_rate": self.fuel_consumption_rate,
            },
            "battery_voltage": self.battery_voltage,
            "dtc_codes": self.dtc_codes,
            "driver_behavior": {
                "harsh_braking": self.harsh_braking,
                "harsh_acceleration": self.harsh_acceleration,
                "sharp_cornering": self.sharp_cornering,
            },
        }
