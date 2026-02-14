"""
Fleet Management System — Main Application Entry Point

Starts the FastAPI server with all routes, initializes the database,
and optionally starts vehicle tracking services.

Usage:
    python main.py                  # Start the API server
    python main.py --seed           # Seed sample data and start
    python simulator.py             # Run telemetry simulator (separate terminal)
"""

import sys
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from models.database import init_db, SessionLocal
from models.vehicle import Vehicle, VehicleStatus, FuelType
from models.driver import Driver
from api.vehicles import router as vehicles_router
from api.telemetry import router as telemetry_router
from api.alerts import router as alerts_router
from api.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fleet_manager")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("  Fleet Management System — Starting Up")
    logger.info("=" * 60)

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Seed sample data if requested
    if "--seed" in sys.argv:
        seed_sample_data()

    logger.info(f"API running at http://localhost:{settings.api.PORT}")
    logger.info(f"Dashboard at http://localhost:{settings.api.PORT}/")
    logger.info(f"API docs at http://localhost:{settings.api.PORT}/docs")
    logger.info("=" * 60)

    yield  # Application is running

    logger.info("Fleet Management System — Shutting Down")


# ── Create FastAPI App ─────────────────────────────────────────

app = FastAPI(
    title="Fleet Management System",
    description="""
    🚗 Automotive Fleet Management with Telematics

    Features:
    - Real-time vehicle tracking via OBD-II, GPS, and CAN bus
    - Diagnostic Trouble Code (DTC) analysis
    - Driver behavior monitoring
    - Fuel consumption analytics
    - Geofence alerts
    - Predictive maintenance scheduling
    - Live fleet dashboard
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(dashboard_router)
app.include_router(vehicles_router, prefix=settings.api.API_PREFIX)
app.include_router(telemetry_router, prefix=settings.api.API_PREFIX)
app.include_router(alerts_router, prefix=settings.api.API_PREFIX)


# ── Health Check ───────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "service": "Fleet Management System", "version": "1.0.0"}


# ── Sample Data Seeder ─────────────────────────────────────────

def seed_sample_data():
    """Populate the database with sample vehicles and drivers."""
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Vehicle).count() > 0:
            logger.info("Database already has data, skipping seed")
            return

        logger.info("Seeding sample fleet data...")

        # Sample vehicles
        vehicles = [
            Vehicle(
                vin="1HGBH41JXMN109186", license_plate="DL-01-AB-1234",
                make="Toyota", model="Camry", year=2024, color="White",
                fuel_type=FuelType.PETROL, engine_capacity=2.5,
                fleet_group="sales", status=VehicleStatus.IDLE,
                current_fuel_level=75.0, odometer=12500,
            ),
            Vehicle(
                vin="2T1BURHE5JC067841", license_plate="DL-02-CD-5678",
                make="Honda", model="City", year=2023, color="Silver",
                fuel_type=FuelType.PETROL, engine_capacity=1.5,
                fleet_group="delivery", status=VehicleStatus.IDLE,
                current_fuel_level=60.0, odometer=28000,
            ),
            Vehicle(
                vin="5YJSA1E26MF123456", license_plate="DL-03-EF-9012",
                make="Tata", model="Nexon EV", year=2025, color="Blue",
                fuel_type=FuelType.ELECTRIC, engine_capacity=0,
                fleet_group="executive", status=VehicleStatus.IDLE,
                current_fuel_level=85.0, odometer=5000,
            ),
            Vehicle(
                vin="WBAJB0C55JB084299", license_plate="MH-01-GH-3456",
                make="Mahindra", model="XUV700", year=2024, color="Red",
                fuel_type=FuelType.DIESEL, engine_capacity=2.2,
                fleet_group="field_ops", status=VehicleStatus.IDLE,
                current_fuel_level=45.0, odometer=42000,
            ),
            Vehicle(
                vin="JN1TBNT30Z0000001", license_plate="KA-01-IJ-7890",
                make="Maruti Suzuki", model="Swift", year=2024, color="Grey",
                fuel_type=FuelType.CNG, engine_capacity=1.2,
                fleet_group="delivery", status=VehicleStatus.IDLE,
                current_fuel_level=90.0, odometer=15000,
            ),
        ]

        for v in vehicles:
            db.add(v)

        # Sample drivers
        drivers = [
            Driver(first_name="Rahul", last_name="Sharma", employee_id="DRV001",
                   email="rahul@fleet.com", phone="+91-9876543210",
                   license_number="DL-0420230012345", safety_score=92.5),
            Driver(first_name="Priya", last_name="Patel", employee_id="DRV002",
                   email="priya@fleet.com", phone="+91-9876543211",
                   license_number="MH-0320240098765", safety_score=88.0),
            Driver(first_name="Amit", last_name="Singh", employee_id="DRV003",
                   email="amit@fleet.com", phone="+91-9876543212",
                   license_number="KA-0120250054321", safety_score=95.0),
        ]

        for d in drivers:
            db.add(d)

        db.commit()
        logger.info(f"Seeded {len(vehicles)} vehicles and {len(drivers)} drivers")

    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}")
    finally:
        db.close()


# ── Run Server ─────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api.HOST,
        port=settings.api.PORT,
        reload=settings.api.DEBUG,
        log_level="info",
    )
