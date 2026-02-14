"""
Vehicle API routes — CRUD operations and vehicle management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from models.database import get_db
from models.vehicle import Vehicle, VehicleStatus, FuelType

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# ── Pydantic Schemas ─────────────────────────────────────────

class VehicleCreate(BaseModel):
    vin: str = Field(..., min_length=17, max_length=17, description="17-char Vehicle Identification Number")
    license_plate: str
    make: str
    model: str
    year: int = Field(..., ge=1990, le=2030)
    color: Optional[str] = None
    fuel_type: FuelType = FuelType.PETROL
    engine_capacity: Optional[float] = None
    transmission: str = "automatic"
    fleet_group: str = "default"
    telematics_device_id: Optional[str] = None


class VehicleUpdate(BaseModel):
    license_plate: Optional[str] = None
    color: Optional[str] = None
    status: Optional[VehicleStatus] = None
    fleet_group: Optional[str] = None
    telematics_device_id: Optional[str] = None
    is_active: Optional[bool] = None


class VehicleResponse(BaseModel):
    id: int
    vin: str
    license_plate: str
    make: str
    model: str
    year: int
    color: Optional[str]
    fuel_type: str
    status: str
    fleet_group: str
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    current_speed: float
    current_fuel_level: float
    odometer: float
    is_active: bool
    created_at: datetime
    last_telemetry_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── API Endpoints ─────────────────────────────────────────────

@router.post("/", response_model=VehicleResponse, status_code=201)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    """Register a new vehicle in the fleet."""
    # Check for duplicate VIN
    existing = db.query(Vehicle).filter(Vehicle.vin == vehicle.vin).first()
    if existing:
        raise HTTPException(400, f"Vehicle with VIN {vehicle.vin} already exists")

    db_vehicle = Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.get("/", response_model=List[VehicleResponse])
def list_vehicles(
    status: Optional[VehicleStatus] = None,
    fleet_group: Optional[str] = None,
    is_active: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all vehicles with optional filters."""
    query = db.query(Vehicle).filter(Vehicle.is_active == is_active)
    if status:
        query = query.filter(Vehicle.status == status)
    if fleet_group:
        query = query.filter(Vehicle.fleet_group == fleet_group)
    return query.offset(skip).limit(limit).all()


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get a specific vehicle by ID."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, update: VehicleUpdate, db: Session = Depends(get_db)):
    """Update vehicle details."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Deactivate a vehicle (soft delete)."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    vehicle.is_active = False
    db.commit()
    return {"message": f"Vehicle {vehicle.license_plate} deactivated"}


@router.get("/{vehicle_id}/location")
def get_vehicle_location(vehicle_id: int, db: Session = Depends(get_db)):
    """Get current vehicle GPS location."""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    return {
        "vehicle_id": vehicle.id,
        "license_plate": vehicle.license_plate,
        "latitude": vehicle.current_latitude,
        "longitude": vehicle.current_longitude,
        "speed": vehicle.current_speed,
        "last_update": vehicle.last_telemetry_at,
    }


@router.get("/fleet/summary")
def fleet_summary(db: Session = Depends(get_db)):
    """Get fleet-wide statistics."""
    total = db.query(Vehicle).filter(Vehicle.is_active == True).count()
    active = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).count()
    idle = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.IDLE).count()
    in_transit = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.IN_TRANSIT).count()
    maintenance = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.MAINTENANCE).count()
    out_of_service = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.OUT_OF_SERVICE).count()

    return {
        "total_vehicles": total,
        "active": active,
        "idle": idle,
        "in_transit": in_transit,
        "maintenance": maintenance,
        "out_of_service": out_of_service,
    }
