"""
Maintenance record model — tracks service history and upcoming maintenance.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.database import Base


class MaintenanceType(str, enum.Enum):
    OIL_CHANGE = "oil_change"
    TIRE_ROTATION = "tire_rotation"
    BRAKE_SERVICE = "brake_service"
    FILTER_REPLACEMENT = "filter_replacement"
    BATTERY_REPLACEMENT = "battery_replacement"
    TRANSMISSION_SERVICE = "transmission_service"
    ENGINE_DIAGNOSTIC = "engine_diagnostic"
    SCHEDULED_SERVICE = "scheduled_service"
    REPAIR = "repair"
    INSPECTION = "inspection"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)

    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False)
    status = Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED)
    description = Column(String(500), nullable=True)

    # Schedule
    scheduled_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    scheduled_odometer = Column(Float, nullable=True)   # trigger at this mileage

    # Cost
    cost = Column(Float, default=0.0)
    service_provider = Column(String(100), nullable=True)

    # Parts
    parts_replaced = Column(String(500), nullable=True)

    # Triggered by DTC?
    triggered_by_dtc = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")

    def __repr__(self):
        return f"<Maintenance {self.maintenance_type.value} vehicle={self.vehicle_id} status={self.status.value}>"
