"""
Trip model — tracks individual trips from ignition-on to ignition-off.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from models.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id = Column(Integer, nullable=True)

    # Trip Boundaries
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Start Location
    start_latitude = Column(Float, nullable=True)
    start_longitude = Column(Float, nullable=True)
    start_address = Column(String(200), nullable=True)

    # End Location
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)
    end_address = Column(String(200), nullable=True)

    # Trip Metrics
    distance_km = Column(Float, default=0.0)
    duration_minutes = Column(Float, default=0.0)
    avg_speed = Column(Float, default=0.0)           # km/h
    max_speed = Column(Float, default=0.0)           # km/h
    fuel_consumed = Column(Float, default=0.0)       # liters
    fuel_efficiency = Column(Float, nullable=True)   # km/L

    # Driver Behavior Summary
    harsh_brake_count = Column(Integer, default=0)
    harsh_accel_count = Column(Integer, default=0)
    speeding_duration_sec = Column(Integer, default=0)
    idle_duration_sec = Column(Integer, default=0)
    trip_score = Column(Float, default=100.0)        # 0-100

    # Odometer
    start_odometer = Column(Float, nullable=True)
    end_odometer = Column(Float, nullable=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="trips")

    def __repr__(self):
        return f"<Trip vehicle={self.vehicle_id} dist={self.distance_km}km>"
