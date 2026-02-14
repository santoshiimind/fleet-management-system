"""
Geofence model — virtual geographic boundaries for fleet monitoring.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime

from models.database import Base


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=True)

    # Circle-based geofence (center + radius)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, nullable=False, default=5000.0)

    # Settings
    alert_on_entry = Column(Boolean, default=False)
    alert_on_exit = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Applicable to specific fleet group (None = all)
    fleet_group = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Geofence '{self.name}' r={self.radius_meters}m>"
