"""Quick test script for the Fleet Management API."""
import requests
import json

API = "http://127.0.0.1:8000/api/v1"

# List vehicles
r = requests.get(f"{API}/vehicles/")
print("=== VEHICLES ===")
for v in r.json():
    print(f"  #{v['id']} {v['make']} {v['model']} ({v['license_plate']}) - {v['status']}")

# Fleet summary
r = requests.get(f"{API}/vehicles/fleet/summary")
print(f"\n=== FLEET SUMMARY ===")
print(json.dumps(r.json(), indent=2))

# Test telemetry ingest
data = {
    "vehicle_id": 1, "latitude": 28.6139, "longitude": 77.2090,
    "vehicle_speed": 85.5, "engine_rpm": 3200, "coolant_temp": 92.0,
    "fuel_level": 65.0, "battery_voltage": 13.8, "odometer": 12550
}
r = requests.post(f"{API}/telemetry/ingest", json=data)
print(f"\n=== TELEMETRY INGEST ===")
print(json.dumps(r.json(), indent=2))

# Get alerts
r = requests.get(f"{API}/alerts/")
print(f"\n=== ALERTS ({len(r.json())}) ===")
for a in r.json()[:5]:
    print(f"  [{a['severity']}] {a['message']}")

print("\n All tests passed!")
