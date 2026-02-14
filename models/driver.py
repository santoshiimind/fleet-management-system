"""
Driver model — represents a driver assigned to fleet vehicles.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)

    # Personal Info
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    employee_id = Column(String(30), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    license_number = Column(String(50), nullable=False)
    license_expiry = Column(Date, nullable=True)

    # Assignment
    assigned_vehicle_id = Column(Integer, nullable=True)  # current vehicle
    is_active = Column(Boolean, default=True)

    # Driving Score (computed from telematics)
    safety_score = Column(Float, default=100.0)    # 0-100
    total_distance_km = Column(Float, default=0.0)
    total_trips = Column(Integer, default=0)
    harsh_events_count = Column(Integer, default=0)
    speeding_events_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Driver {self.first_name} {self.last_name} ({self.employee_id})>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
