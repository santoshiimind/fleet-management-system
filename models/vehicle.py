"""
Vehicle model — represents a car/truck in the fleet.
Stores static info (VIN, make, model) and current status.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.database import Base


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    IN_TRANSIT = "in_transit"


class FuelType(str, enum.Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    CNG = "cng"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)

    # Vehicle Identification
    vin = Column(String(17), unique=True, nullable=False, index=True)  # ISO 3779 VIN
    license_plate = Column(String(20), unique=True, nullable=False)
    registration_number = Column(String(50), nullable=True)

    # Vehicle Details
    make = Column(String(50), nullable=False)          # e.g., Toyota, Ford
    model = Column(String(50), nullable=False)          # e.g., Camry, F-150
    year = Column(Integer, nullable=False)
    color = Column(String(30), nullable=True)
    fuel_type = Column(SQLEnum(FuelType), default=FuelType.PETROL)
    engine_capacity = Column(Float, nullable=True)      # liters
    transmission = Column(String(20), default="automatic")

    # Telematics Device
    telematics_device_id = Column(String(50), unique=True, nullable=True)
    obd_protocol = Column(String(30), default="AUTO")   # OBD-II protocol

    # Fleet Info
    fleet_group = Column(String(50), default="default")
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.IDLE)
    is_active = Column(Boolean, default=True)

    # Current State (updated by telematics)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_speed = Column(Float, default=0.0)           # km/h
    current_fuel_level = Column(Float, default=100.0)     # percentage
    odometer = Column(Float, default=0.0)                 # km
    engine_hours = Column(Float, default=0.0)             # total engine hours

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_telemetry_at = Column(DateTime, nullable=True)

    # Relationships
    telemetry_data = relationship("TelemetryData", back_populates="vehicle", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="vehicle", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vehicle {self.make} {self.model} ({self.license_plate})>"

    @property
    def display_name(self):
        return f"{self.year} {self.make} {self.model}"
