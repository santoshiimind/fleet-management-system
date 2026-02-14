"""
Telemetry Simulator — Generates realistic vehicle telemetry data for testing.

Simulates multiple vehicles driving around with realistic:
- GPS routes with turn-by-turn movement
- Engine RPM patterns based on speed
- Fuel consumption that drains over time
- Occasional DTC faults
- Driver behavior events (harsh braking, acceleration)
"""

import random
import math
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class VehicleSimulator:
    """Simulates a single vehicle's telematics data."""

    def __init__(self, vehicle_id: int, start_lat: float = 28.6139, start_lon: float = 77.2090):
        self.vehicle_id = vehicle_id
        self.lat = start_lat + random.uniform(-0.02, 0.02)
        self.lon = start_lon + random.uniform(-0.02, 0.02)
        self.speed = 0.0
        self.heading = random.uniform(0, 360)
        self.fuel_level = random.uniform(40, 100)
        self.odometer = random.uniform(5000, 80000)
        self.engine_rpm = 800
        self.coolant_temp = 85.0
        self.battery_voltage = 12.6
        self.is_driving = True
        self._trip_progress = 0
        self._speed_target = random.uniform(40, 100)

    def tick(self) -> Dict:
        """Generate one telemetry snapshot."""
        # Randomly start/stop driving
        if random.random() < 0.02:
            self.is_driving = not self.is_driving

        if self.is_driving:
            self._update_driving()
        else:
            self._update_idle()

        # Occasionally change direction
        if random.random() < 0.1:
            self.heading += random.uniform(-45, 45)
            self.heading %= 360

        # Occasional DTC
        dtcs = None
        if random.random() < 0.005:  # 0.5% chance per tick
            dtc_pool = ["P0301", "P0420", "P0171", "P0128", "P0442", "P0300", "P0115"]
            dtcs = random.sample(dtc_pool, random.randint(1, 2))

        # Driver behavior events
        accel_x = random.uniform(-2, 2)
        accel_y = random.uniform(-3, 3)

        # Occasional harsh events
        if random.random() < 0.02 and self.speed > 40:
            accel_y = random.choice([-10, -9, 7, 6])  # harsh brake or accel

        return {
            "vehicle_id": self.vehicle_id,
            "latitude": round(self.lat, 6),
            "longitude": round(self.lon, 6),
            "altitude": round(random.uniform(200, 250), 1),
            "heading": round(self.heading, 1),
            "gps_speed": round(self.speed, 1),
            "vehicle_speed": round(self.speed + random.uniform(-2, 2), 1),
            "engine_rpm": round(self.engine_rpm, 0),
            "throttle_position": round(max(0, min(100, self.speed * 0.6 + random.uniform(-5, 5))), 1),
            "engine_load": round(max(5, min(95, self.speed * 0.5 + random.uniform(-10, 10))), 1),
            "coolant_temp": round(self.coolant_temp, 1),
            "intake_air_temp": round(random.uniform(25, 45), 1),
            "mass_air_flow": round(max(2, self.engine_rpm * 0.003 + random.uniform(-1, 1)), 2),
            "fuel_level": round(self.fuel_level, 1),
            "fuel_consumption_rate": round(max(0.5, self.speed * 0.08 + random.uniform(-1, 1)), 2),
            "battery_voltage": round(self.battery_voltage, 2),
            "engine_oil_temp": round(self.coolant_temp + random.uniform(-5, 15), 1),
            "odometer": round(self.odometer, 1),
            "dtc_codes": dtcs,
            "acceleration_x": round(accel_x, 2),
            "acceleration_y": round(accel_y, 2),
            "acceleration_z": round(random.uniform(-1, 1), 2),
        }

    def _update_driving(self):
        """Update state for a vehicle in motion."""
        # Adjust speed toward target
        speed_diff = self._speed_target - self.speed
        self.speed += speed_diff * 0.1 + random.uniform(-3, 3)
        self.speed = max(0, min(160, self.speed))

        # Occasionally change target speed (traffic, signals)
        if random.random() < 0.05:
            self._speed_target = random.uniform(20, 110)

        # Update position based on speed and heading
        speed_mps = self.speed / 3.6  # km/h to m/s
        distance = speed_mps * 2  # 2-second interval
        self.lat += (distance * math.cos(math.radians(self.heading))) / 111320
        self.lon += (distance * math.sin(math.radians(self.heading))) / (111320 * math.cos(math.radians(self.lat)))

        # Engine RPM correlates with speed
        self.engine_rpm = max(750, min(6000, self.speed * 30 + random.uniform(-200, 200)))

        # Fuel consumption
        self.fuel_level -= random.uniform(0.01, 0.05)
        self.fuel_level = max(0, self.fuel_level)

        # Odometer
        self.odometer += distance / 1000  # meters to km

        # Coolant temp (warms up when driving)
        self.coolant_temp += random.uniform(-0.5, 0.5)
        self.coolant_temp = max(80, min(110, self.coolant_temp))

        # Battery voltage (alternator charging)
        self.battery_voltage = 13.5 + random.uniform(-0.5, 0.5)

    def _update_idle(self):
        """Update state for a stationary vehicle."""
        self.speed = max(0, self.speed * 0.5)
        self.engine_rpm = 800 + random.uniform(-50, 50)
        self.fuel_level -= random.uniform(0.001, 0.005)
        self.coolant_temp += random.uniform(-1, 0.5)
        self.coolant_temp = max(60, min(95, self.coolant_temp))
        self.battery_voltage = 12.4 + random.uniform(-0.3, 0.3)


def run_simulator(
    api_url: str = "http://localhost:8000/api/v1/telemetry/ingest",
    vehicle_ids: List[int] = None,
    interval: float = 2.0,
    duration: int = 0,
):
    """
    Run the fleet simulator, sending telemetry data to the API.

    Args:
        api_url: URL of the telemetry ingest endpoint
        vehicle_ids: List of vehicle IDs to simulate (default: [1, 2, 3])
        interval: Seconds between telemetry updates
        duration: Total seconds to run (0 = run forever)
    """
    if vehicle_ids is None:
        vehicle_ids = [1, 2, 3]

    simulators = {vid: VehicleSimulator(vid) for vid in vehicle_ids}

    print(f"\n{'='*60}")
    print(f"  🚗 Fleet Telemetry Simulator")
    print(f"{'='*60}")
    print(f"  Vehicles: {vehicle_ids}")
    print(f"  API: {api_url}")
    print(f"  Interval: {interval}s")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*60}\n")

    start_time = time.time()
    tick_count = 0

    try:
        while True:
            for vid, sim in simulators.items():
                data = sim.tick()

                try:
                    response = requests.post(api_url, json=data, timeout=5)
                    status = response.status_code
                    alerts = response.json().get("alerts_triggered", 0) if status == 201 else 0

                    if tick_count % 10 == 0:  # Print every 10th tick to reduce noise
                        print(
                            f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"Vehicle #{vid}: "
                            f"speed={data['vehicle_speed']:.0f}km/h  "
                            f"fuel={data['fuel_level']:.0f}%  "
                            f"rpm={data['engine_rpm']:.0f}  "
                            f"pos=({data['latitude']:.4f}, {data['longitude']:.4f})  "
                            f"alerts={alerts}"
                        )
                except requests.exceptions.ConnectionError:
                    if tick_count % 30 == 0:
                        print(f"⚠ Cannot connect to API at {api_url}. Is the server running?")
                except Exception as e:
                    logger.error(f"Simulator error: {e}")

            tick_count += 1
            if duration > 0 and (time.time() - start_time) >= duration:
                print("\nSimulation duration reached. Stopping.")
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nSimulator stopped by user.")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Parse command line args
    vehicle_ids = [1, 2, 3]
    if len(sys.argv) > 1:
        vehicle_ids = [int(x) for x in sys.argv[1].split(",")]

    run_simulator(vehicle_ids=vehicle_ids)
