"""
Dashboard API routes — Serves the web dashboard and provides dashboard data.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta

from models.database import get_db
from models.vehicle import Vehicle, VehicleStatus
from models.alert import Alert, AlertSeverity
from models.telemetry import TelemetryData
from models.trip import Trip

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page."""
    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    recent_alerts = (
        db.query(Alert)
        .filter(Alert.is_acknowledged == False)
        .order_by(desc(Alert.created_at))
        .limit(10)
        .all()
    )

    # Fleet stats
    total_vehicles = len(vehicles)
    active_count = sum(1 for v in vehicles if v.status == VehicleStatus.IN_TRANSIT)
    idle_count = sum(1 for v in vehicles if v.status == VehicleStatus.IDLE)
    maintenance_count = sum(1 for v in vehicles if v.status == VehicleStatus.MAINTENANCE)

    # Alert stats
    critical_alerts = sum(1 for a in recent_alerts if a.severity == AlertSeverity.CRITICAL)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "vehicles": vehicles,
        "recent_alerts": recent_alerts,
        "stats": {
            "total_vehicles": total_vehicles,
            "active": active_count,
            "idle": idle_count,
            "maintenance": maintenance_count,
            "critical_alerts": critical_alerts,
            "total_alerts": len(recent_alerts),
        },
    })


@router.get("/api/v1/dashboard/fleet-map")
def fleet_map_data(db: Session = Depends(get_db)):
    """Get all vehicle locations for the fleet map."""
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_active == True, Vehicle.current_latitude.isnot(None))
        .all()
    )
    return [
        {
            "id": v.id,
            "name": f"{v.make} {v.model}",
            "plate": v.license_plate,
            "lat": v.current_latitude,
            "lng": v.current_longitude,
            "speed": v.current_speed,
            "fuel": v.current_fuel_level,
            "status": v.status.value,
            "last_update": v.last_telemetry_at.isoformat() if v.last_telemetry_at else None,
        }
        for v in vehicles
    ]


@router.get("/api/v1/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """Real-time dashboard statistics."""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    today_alerts = db.query(Alert).filter(Alert.created_at >= today).count()

    # Today's trips
    today_trips = db.query(Trip).filter(Trip.start_time >= today).all()
    total_distance = sum(t.distance_km for t in today_trips)
    total_fuel = sum(t.fuel_consumed for t in today_trips)

    return {
        "fleet": {
            "total": len(vehicles),
            "in_transit": sum(1 for v in vehicles if v.status == VehicleStatus.IN_TRANSIT),
            "idle": sum(1 for v in vehicles if v.status == VehicleStatus.IDLE),
            "maintenance": sum(1 for v in vehicles if v.status == VehicleStatus.MAINTENANCE),
        },
        "today": {
            "alerts": today_alerts,
            "trips": len(today_trips),
            "distance_km": round(total_distance, 1),
            "fuel_consumed_liters": round(total_fuel, 1),
        },
        "timestamp": now.isoformat(),
    }
