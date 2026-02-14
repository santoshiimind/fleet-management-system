#!/usr/bin/env python3
"""
Fleet Management System — CLI Entry Point

Production-ready command-line interface for the fleet management platform.

Usage:
    fleet-management run                    # Start production server
    fleet-management run --dev              # Start development server with reload
    fleet-management run --port 9000        # Custom port
    fleet-management seed                   # Seed sample data
    fleet-management check                  # Health check
    fleet-management version                # Show version
"""

import argparse
import sys
import os
import logging

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("fleet_management")


def cmd_run(args):
    """Start the Fleet Management server."""
    import uvicorn
    from config.settings import settings

    host = args.host or settings.api.HOST
    port = args.port or settings.api.PORT

    if args.dev:
        # Development mode with auto-reload
        print(f"🚗 Starting Fleet Management (DEV) at http://{host}:{port}")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="debug",
        )
    else:
        # Production mode
        workers = args.workers or (os.cpu_count() or 1) * 2 + 1

        print(f"🚗 Fleet Management System v1.0.0")
        print(f"   Server:  http://{host}:{port}")
        print(f"   Workers: {workers}")
        print(f"   Docs:    http://{host}:{port}/docs")
        print(f"   Mode:    PRODUCTION")
        print()

        try:
            # Try gunicorn first (Linux/Mac production)
            from gunicorn.app.wsgiapp import run as gunicorn_run
            sys.argv = [
                "gunicorn",
                "main:app",
                "-w", str(workers),
                "-k", "uvicorn.workers.UvicornWorker",
                "-b", f"{host}:{port}",
                "--access-logfile", "-",
                "--error-logfile", "-",
                "--timeout", "120",
                "--graceful-timeout", "30",
                "--keep-alive", "5",
            ]
            gunicorn_run()
        except ImportError:
            # Fallback to uvicorn (Windows or no gunicorn)
            print("   (gunicorn not available, using uvicorn)")
            uvicorn.run(
                "main:app",
                host=host,
                port=port,
                workers=workers,
                log_level="info",
            )


def cmd_seed(args):
    """Seed the database with sample data."""
    from models.database import init_db, SessionLocal
    from models.vehicle import Vehicle, VehicleStatus, FuelType
    from models.driver import Driver

    print("🌱 Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        if db.query(Vehicle).count() > 0 and not args.force:
            print("⚠  Database already has data. Use --force to re-seed.")
            return

        if args.force:
            print("   Clearing existing data...")
            db.query(Driver).delete()
            db.query(Vehicle).delete()
            db.commit()

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

        for v in vehicles:
            db.add(v)
        for d in drivers:
            db.add(d)

        db.commit()
        print(f"✅ Seeded {len(vehicles)} vehicles and {len(drivers)} drivers")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        sys.exit(1)
    finally:
        db.close()


def cmd_check(args):
    """Run health checks."""
    import requests

    host = args.host or "127.0.0.1"
    port = args.port or 8000
    url = f"http://{host}:{port}/health"

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("status") == "healthy":
            print(f"✅ Fleet Management is healthy ({url})")
            print(f"   Version: {data.get('version', 'unknown')}")
        else:
            print(f"⚠  Unhealthy response: {data}")
            sys.exit(1)
    except requests.ConnectionError:
        print(f"❌ Cannot connect to {url} — is the server running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)


def cmd_version(args):
    """Show version information."""
    print("Fleet Management System v1.0.0")
    print("Author: Santosh Kumar")
    print("License: Apache License 2.0")
    print("Repository: https://github.com/santoshiimind/fleet-management-system")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="fleet-management",
        description="🚗 Fleet Management System — Automotive Telematics Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fleet-management run                Start production server
  fleet-management run --dev          Start dev server with hot reload
  fleet-management run --port 9000    Custom port
  fleet-management seed               Seed sample data
  fleet-management seed --force       Re-seed (clear + seed)
  fleet-management check              Health check a running server
  fleet-management version            Show version info
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── run ──
    run_parser = subparsers.add_parser("run", help="Start the fleet management server")
    run_parser.add_argument("--dev", action="store_true", help="Development mode with auto-reload")
    run_parser.add_argument("--host", type=str, default=None, help="Bind host (default: 0.0.0.0)")
    run_parser.add_argument("--port", type=int, default=None, help="Bind port (default: 8000)")
    run_parser.add_argument("--workers", type=int, default=None, help="Number of worker processes")
    run_parser.set_defaults(func=cmd_run)

    # ── seed ──
    seed_parser = subparsers.add_parser("seed", help="Seed sample data into the database")
    seed_parser.add_argument("--force", action="store_true", help="Clear existing data and re-seed")
    seed_parser.set_defaults(func=cmd_seed)

    # ── check ──
    check_parser = subparsers.add_parser("check", help="Health check the running server")
    check_parser.add_argument("--host", type=str, default=None, help="Server host")
    check_parser.add_argument("--port", type=int, default=None, help="Server port")
    check_parser.set_defaults(func=cmd_check)

    # ── version ──
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.set_defaults(func=cmd_version)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
