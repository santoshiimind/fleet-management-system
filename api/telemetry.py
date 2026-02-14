"""
Telemetry API routes — Ingest and query vehicle telemetry data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from models.database import get_db
from models.vehicle import Vehicle
from models.telemetry import TelemetryData
from models.alert import Alert
from telematics.alert_engine import AlertEngine

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])
alert_engine = AlertEngine()


# ── Schemas ───────────────────────────────────────────────────

class TelemetryIngest(BaseModel):
    """Schema for ingesting telemetry data from a vehicle device."""
    vehicle_id: int

    # GPS
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    gps_speed: Optional[float] = None

    # OBD-II
    engine_rpm: Optional[float] = None
    vehicle_speed: Optional[float] = None
    throttle_position: Optional[float] = None
    engine_load: Optional[float] = None
    coolant_temp: Optional[float] = None
    intake_air_temp: Optional[float] = None
    mass_air_flow: Optional[float] = None
    fuel_level: Optional[float] = None
    fuel_consumption_rate: Optional[float] = None
    battery_voltage: Optional[float] = None
    engine_oil_temp: Optional[float] = None

    # DTCs
    dtc_codes: Optional[list] = None

    # Accelerometer
    acceleration_x: Optional[float] = None
    acceleration_y: Optional[float] = None
    acceleration_z: Optional[float] = None

    # Odometer
    odometer: Optional[float] = None


class TelemetryResponse(BaseModel):
    id: int
    vehicle_id: int
    timestamp: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    vehicle_speed: Optional[float]
    engine_rpm: Optional[float]
    coolant_temp: Optional[float]
    fuel_level: Optional[float]
    battery_voltage: Optional[float]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/ingest", status_code=201)
def ingest_telemetry(data: TelemetryIngest, db: Session = Depends(get_db)):
    """
    Ingest telemetry data from a vehicle telematics device.

    This is the primary endpoint called by in-vehicle devices to report
    their sensor data. It:
    1. Stores the telemetry record
    2. Updates the vehicle's current state
    3. Evaluates alert conditions
    4. Returns any triggered alerts
    """
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    # Store telemetry record
    telemetry = TelemetryData(**data.model_dump())
    db.add(telemetry)

    # Update vehicle current state
    if data.latitude is not None:
        vehicle.current_latitude = data.latitude
    if data.longitude is not None:
        vehicle.current_longitude = data.longitude
    if data.vehicle_speed is not None:
        vehicle.current_speed = data.vehicle_speed
    elif data.gps_speed is not None:
        vehicle.current_speed = data.gps_speed
    if data.fuel_level is not None:
        vehicle.current_fuel_level = data.fuel_level
    if data.odometer is not None:
        vehicle.odometer = data.odometer
    vehicle.last_telemetry_at = datetime.utcnow()

    # Evaluate alerts
    telemetry_dict = data.model_dump()
    triggered_alerts = alert_engine.evaluate(vehicle.id, telemetry_dict)

    # Store alerts in database
    for alert_data in triggered_alerts:
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

    return {
        "status": "ok",
        "vehicle_id": data.vehicle_id,
        "alerts_triggered": len(triggered_alerts),
        "alerts": [{"type": a["alert_type"].value, "severity": a["severity"].value, "message": a["message"]} for a in triggered_alerts],
    }


@router.get("/{vehicle_id}/latest", response_model=TelemetryResponse)
def get_latest_telemetry(vehicle_id: int, db: Session = Depends(get_db)):
    """Get the most recent telemetry data for a vehicle."""
    record = (
        db.query(TelemetryData)
        .filter(TelemetryData.vehicle_id == vehicle_id)
        .order_by(desc(TelemetryData.timestamp))
        .first()
    )
    if not record:
        raise HTTPException(404, "No telemetry data found")
    return record


@router.get("/{vehicle_id}/history")
def get_telemetry_history(
    vehicle_id: int,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    """Get historical telemetry data for a vehicle."""
    since = datetime.utcnow() - timedelta(hours=hours)
    records = (
        db.query(TelemetryData)
        .filter(TelemetryData.vehicle_id == vehicle_id, TelemetryData.timestamp >= since)
        .order_by(desc(TelemetryData.timestamp))
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in records]


@router.get("/{vehicle_id}/diagnostics")
def get_vehicle_diagnostics(vehicle_id: int, db: Session = Depends(get_db)):
    """Get latest diagnostics (DTCs) for a vehicle."""
    from telematics.dtc_analyzer import DTCAnalyzer

    latest = (
        db.query(TelemetryData)
        .filter(TelemetryData.vehicle_id == vehicle_id, TelemetryData.dtc_codes.isnot(None))
        .order_by(desc(TelemetryData.timestamp))
        .first()
    )

    if not latest or not latest.dtc_codes:
        return {"vehicle_id": vehicle_id, "dtc_codes": [], "analysis": None}

    analyzer = DTCAnalyzer()
    codes = [c if isinstance(c, str) else c.get("code", "") for c in latest.dtc_codes]
    analysis = analyzer.analyze(codes)

    return {
        "vehicle_id": vehicle_id,
        "timestamp": latest.timestamp,
        "analysis": analysis,
    }


@router.get("/{vehicle_id}/fuel-analytics")
def get_fuel_analytics(
    vehicle_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get fuel consumption analytics for a vehicle."""
    since = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(TelemetryData)
        .filter(
            TelemetryData.vehicle_id == vehicle_id,
            TelemetryData.timestamp >= since,
            TelemetryData.fuel_level.isnot(None),
        )
        .order_by(TelemetryData.timestamp)
        .all()
    )

    if not records:
        return {"vehicle_id": vehicle_id, "data_points": 0, "message": "No fuel data available"}

    fuel_levels = [r.fuel_level for r in records if r.fuel_level is not None]
    consumption_rates = [r.fuel_consumption_rate for r in records if r.fuel_consumption_rate is not None]

    return {
        "vehicle_id": vehicle_id,
        "period_days": days,
        "data_points": len(records),
        "current_fuel_level": fuel_levels[-1] if fuel_levels else None,
        "avg_fuel_level": round(sum(fuel_levels) / len(fuel_levels), 1) if fuel_levels else None,
        "avg_consumption_rate": round(sum(consumption_rates) / len(consumption_rates), 2) if consumption_rates else None,
        "min_fuel_level": min(fuel_levels) if fuel_levels else None,
    }
