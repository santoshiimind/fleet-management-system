"""Capture a screenshot of the fleet dashboard for the README."""
import requests
import json
import time
import random

API = "http://127.0.0.1:8000/api/v1"

# Inject realistic telemetry data for all 5 vehicles to make the dashboard look live
print("Injecting telemetry data for realistic dashboard...")

vehicles_data = [
    {"vehicle_id": 1, "latitude": 28.6139, "longitude": 77.2090, "vehicle_speed": 72.5, "engine_rpm": 2800,
     "coolant_temp": 91.0, "fuel_level": 68.0, "battery_voltage": 13.8, "odometer": 12800},
    {"vehicle_id": 2, "latitude": 28.6350, "longitude": 77.2250, "vehicle_speed": 45.0, "engine_rpm": 2100,
     "coolant_temp": 88.0, "fuel_level": 52.0, "battery_voltage": 13.5, "odometer": 28500},
    {"vehicle_id": 3, "latitude": 28.5900, "longitude": 77.1950, "vehicle_speed": 0, "engine_rpm": 0,
     "coolant_temp": 45.0, "fuel_level": 82.0, "battery_voltage": 12.8, "odometer": 5100},
    {"vehicle_id": 4, "latitude": 28.6500, "longitude": 77.2400, "vehicle_speed": 95.0, "engine_rpm": 3500,
     "coolant_temp": 96.0, "fuel_level": 35.0, "battery_voltage": 14.1, "odometer": 42500},
    {"vehicle_id": 5, "latitude": 28.5700, "longitude": 77.1800, "vehicle_speed": 58.0, "engine_rpm": 2400,
     "coolant_temp": 89.0, "fuel_level": 88.0, "battery_voltage": 13.6, "odometer": 15200},
]

# Also trigger some alerts with extreme values
alert_data = [
    {"vehicle_id": 4, "latitude": 28.6500, "longitude": 77.2400, "vehicle_speed": 155.0, "engine_rpm": 5800,
     "coolant_temp": 118.0, "fuel_level": 8.0, "battery_voltage": 14.1, "odometer": 42510},
    {"vehicle_id": 2, "latitude": 28.6350, "longitude": 77.2250, "vehicle_speed": 125.0, "engine_rpm": 4200,
     "coolant_temp": 102.0, "fuel_level": 12.0, "battery_voltage": 11.2, "odometer": 28520},
]

for data in vehicles_data:
    r = requests.post(f"{API}/telemetry/ingest", json=data)
    print(f"  Vehicle #{data['vehicle_id']}: {r.status_code}")

time.sleep(0.5)

for data in alert_data:
    r = requests.post(f"{API}/telemetry/ingest", json=data)
    result = r.json()
    print(f"  Vehicle #{data['vehicle_id']} (alerts): {result.get('alerts_triggered', 0)} alerts triggered")

print("\nCapturing dashboard screenshot...")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Let animations complete
    
    page.screenshot(path="screenshots/dashboard.png", full_page=True)
    print("Screenshot saved to screenshots/dashboard.png")
    
    browser.close()

print("Done!")
