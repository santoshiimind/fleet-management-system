# 🚗 Fleet Management System — Automotive Telematics

A comprehensive **Python-based fleet management platform** with real-time vehicle telematics, designed for the automotive sector.

> **Built with:** Python 3.10+ · FastAPI · SQLAlchemy · OBD-II · CAN Bus · GPS/GNSS

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📸 Live Dashboard Preview

![Fleet Management Dashboard](screenshots/dashboard.png)

*Real-time fleet dashboard showing vehicle tracking, engine telemetry, fuel levels, and active alerts.*

---

## 📌 About

This system provides **end-to-end fleet management** for automotive companies, logistics operators, and transportation businesses. It connects directly to vehicles via **OBD-II, CAN bus, and GPS** to collect real-time telemetry data, enabling fleet operators to:

- **Monitor every vehicle in real-time** — location, speed, engine health, fuel levels
- **Detect and diagnose faults instantly** — 600+ Diagnostic Trouble Codes with severity analysis
- **Improve driver safety** — automatic detection of harsh braking, speeding, aggressive driving
- **Reduce operational costs** — fuel consumption analytics, predictive maintenance scheduling
- **Ensure compliance** — geofence monitoring, trip logging, driver behavior scoring

The platform is designed following **automotive industry standards** (SAE J1979, ISO 11898, NMEA 0183) and is compatible with any vehicle manufactured after 1996 (OBD-II mandatory).

---

## 🎯 Use Cases

### 1. 🚚 Logistics & Delivery Fleet
Track delivery vehicles across cities in real-time. Monitor route adherence, delivery times, and fuel consumption. Get alerts when vehicles deviate from geofenced zones or when drivers speed.

**Key features used:** GPS Tracking, Geofencing, Trip Logging, Fuel Analytics

### 2. 🏢 Corporate Fleet Management
Manage a company's vehicle fleet — from sales team cars to executive vehicles. Track maintenance schedules, ensure vehicles are serviced on time, and monitor driver behavior for insurance compliance.

**Key features used:** Maintenance Scheduling, Driver Safety Scores, Vehicle CRUD, Alerts

### 3. 🚕 Taxi & Ride-Hailing Operations
Monitor cab fleets in real-time. Track idle time, trip distances, fuel efficiency per driver, and identify underperforming vehicles. Automate maintenance alerts based on mileage and engine diagnostics.

**Key features used:** Trip Tracking, Fuel Analytics, OBD-II Diagnostics, Driver Scoring

### 4. 🏗️ Construction & Heavy Equipment
Track construction vehicles and heavy machinery across job sites. Monitor engine hours, overheating, and excessive idling. Schedule preventive maintenance to avoid costly breakdowns.

**Key features used:** Engine Health Monitoring, Idle Alerts, Maintenance Records, CAN Bus Data

### 5. 🚐 Public Transportation
Monitor buses, shuttles, and municipal vehicles. Ensure route compliance, track real-time passenger vehicle locations, and maintain vehicle health across a large fleet.

**Key features used:** GPS Tracking, Geofencing, Fleet Dashboard, Alert Engine

### 6. 🔧 Vehicle Diagnostics Workshop
Use the DTC Analyzer as a diagnostic tool. Connect to customer vehicles via OBD-II, read fault codes, get severity assessments, and generate repair recommendations with cost estimates.

**Key features used:** OBD-II Reader, DTC Analyzer, Maintenance Suggestions

### 7. 📊 Insurance Telematics (UBI)
Implement Usage-Based Insurance by collecting driving behavior data — speed patterns, braking habits, acceleration profiles. Generate driver safety scores for premium calculations.

**Key features used:** Driver Behavior Monitoring, Safety Scores, Trip Analytics, Telemetry History

### 8. 🔋 EV Fleet Management
Monitor electric vehicle fleets with battery level tracking (via fuel_level), charging patterns, and range estimation. Track energy consumption efficiency across the fleet.

**Key features used:** Battery Monitoring, Fuel/Energy Analytics, Vehicle Status Tracking

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (Jinja2)                    │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI REST API                          │
├──────────┬──────────┬───────────┬──────────┬───────────────┤
│ Vehicle  │ Fleet    │ Telematics│ Alert    │ Diagnostics   │
│ Manager  │ Manager  │ Engine    │ Engine   │ (DTC)         │
├──────────┴──────────┴───────────┴──────────┴───────────────┤
│               SQLAlchemy ORM + SQLite/PostgreSQL            │
├─────────────────────────────────────────────────────────────┤
│  OBD-II  │  GPS     │  CAN Bus  │  MQTT    │  Simulator   │
│  Reader  │  Tracker │  Decoder  │  (opt)   │  (testing)   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
FLEETMANAGMENT/
├── main.py                    # Application entry point
├── simulator.py               # Telemetry data simulator
├── requirements.txt           # Python dependencies
│
├── config/
│   └── settings.py            # Centralized configuration
│
├── models/                    # Database models (SQLAlchemy)
│   ├── database.py            # DB engine & session
│   ├── vehicle.py             # Vehicle model (VIN, make, model, status)
│   ├── telemetry.py           # Time-series telemetry data
│   ├── driver.py              # Driver profiles & safety scores
│   ├── alert.py               # Alert records (speeding, DTC, etc.)
│   ├── trip.py                # Trip tracking (start/end, distance)
│   ├── maintenance.py         # Maintenance records & scheduling
│   └── geofence.py            # Virtual geographic boundaries
│
├── telematics/                # Vehicle communication modules
│   ├── obd_reader.py          # OBD-II protocol (SAE J1979)
│   ├── gps_tracker.py         # GPS/GNSS via NMEA 0183
│   ├── can_decoder.py         # CAN bus frame decoding
│   ├── dtc_analyzer.py        # Diagnostic Trouble Code analysis
│   └── alert_engine.py        # Real-time alert evaluation
│
├── services/
│   └── tracking_service.py    # Vehicle tracking orchestrator
│
├── api/                       # FastAPI REST endpoints
│   ├── vehicles.py            # Vehicle CRUD
│   ├── telemetry.py           # Telemetry ingest & query
│   ├── alerts.py              # Alert management
│   └── dashboard.py           # Web dashboard
│
├── templates/
│   └── dashboard.html         # Fleet dashboard UI
│
└── data/                      # SQLite database (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd FLEETMANAGMENT
pip install -r requirements.txt
```

### 2. Start the Server (with sample data)
```bash
python main.py --seed
```

### 3. Open the Dashboard
- **Dashboard:** http://localhost:8000/
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 4. Run the Simulator (separate terminal)
```bash
python simulator.py
```

---

## 🔌 Telematics Features

### OBD-II Diagnostics (`telematics/obd_reader.py`)
Reads real-time data from the vehicle's ECU via the OBD-II port:
- Engine RPM, vehicle speed, throttle position
- Coolant temperature, oil temperature
- Fuel level, fuel consumption rate
- Battery voltage
- Diagnostic Trouble Codes (DTCs)

**Protocols supported:** SAE J1850, ISO 9141, ISO 14230 (KWP), ISO 15765 (CAN)

### GPS Tracking (`telematics/gps_tracker.py`)
Real-time vehicle positioning via NMEA 0183 protocol:
- Latitude/Longitude/Altitude
- Speed and heading from GPS
- Satellite count for fix quality
- Geofence boundary checking (Haversine formula)

### CAN Bus Decoding (`telematics/can_decoder.py`)
Direct vehicle network data access:
- Engine data (RPM, torque, temperatures)
- Wheel speeds, brake pressure, ABS status
- Transmission data (gear, temp)
- Fuel system data
- Battery and electrical system

### DTC Analysis (`telematics/dtc_analyzer.py`)
Intelligent diagnostic trouble code interpretation:
- **600+ DTC codes** in the database (P, C, B, U codes)
- Severity assessment (critical → low)
- Safety recommendations
- Maintenance suggestions with cost estimates
- Supports SAE J2012 standard codes

### Alert Engine (`telematics/alert_engine.py`)
Real-time monitoring with configurable thresholds:
- 🚨 **Speeding** — Warning at 120 km/h, critical at 150 km/h
- 🌡️ **Engine overheat** — Warning at 100°C, critical at 115°C
- ⛽ **Low fuel** — Warning at 15%, critical at 5%
- 🔋 **Low battery** — Warning below 11.5V
- 🛑 **Harsh braking** — Deceleration > 8 m/s²
- 🏎️ **Harsh acceleration** — Acceleration > 5 m/s²
- 📍 **Geofence violations** — Entry/exit alerts
- 🔧 **DTC detection** — Automatic fault alerts

---

## 📡 API Endpoints

### Vehicles
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/vehicles/` | Register a new vehicle |
| GET    | `/api/v1/vehicles/` | List all vehicles |
| GET    | `/api/v1/vehicles/{id}` | Get vehicle details |
| PUT    | `/api/v1/vehicles/{id}` | Update vehicle |
| DELETE | `/api/v1/vehicles/{id}` | Deactivate vehicle |
| GET    | `/api/v1/vehicles/{id}/location` | Get GPS location |
| GET    | `/api/v1/vehicles/fleet/summary` | Fleet statistics |

### Telemetry
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/telemetry/ingest` | Ingest telemetry data |
| GET    | `/api/v1/telemetry/{id}/latest` | Latest reading |
| GET    | `/api/v1/telemetry/{id}/history` | Historical data |
| GET    | `/api/v1/telemetry/{id}/diagnostics` | DTC analysis |
| GET    | `/api/v1/telemetry/{id}/fuel-analytics` | Fuel stats |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/v1/alerts/` | List alerts (filtered) |
| PUT    | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| GET    | `/api/v1/alerts/summary` | Alert statistics |

---

## 🔧 Configuration

All settings are in `config/settings.py` and can be overridden via environment variables:

```bash
# Database
DB_DB_URL=postgresql://user:pass@localhost/fleet

# OBD-II
TELEM_OBD_PORT=COM3
TELEM_OBD_BAUDRATE=9600

# GPS
TELEM_GPS_PORT=COM4

# CAN Bus
TELEM_CAN_INTERFACE=pcan
TELEM_CAN_CHANNEL=PCAN_USBBUS1

# Alert Thresholds
ALERT_SPEED_LIMIT_WARNING=120
ALERT_ENGINE_TEMP_CRITICAL=115

# API
API_PORT=8000
API_DEBUG=true
```

---

## 🏭 Hardware Integration (Production)

For real vehicle connectivity, install the optional packages:

```bash
pip install obd          # ELM327 OBD-II adapter
pip install python-can   # CAN bus (PCAN, Vector, Kvaser)
pip install pyserial     # GPS serial communication
pip install paho-mqtt    # MQTT for IoT messaging
```

**Recommended hardware:**
- **OBD-II:** ELM327 Bluetooth/USB adapter
- **GPS:** u-blox M8N/M9N GNSS module
- **CAN:** PEAK PCAN-USB adapter
- **Telematics unit:** Raspberry Pi + CAN HAT + GPS module

---

## 📊 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Web Framework | FastAPI |
| Database ORM | SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Dashboard | Jinja2 + HTML/CSS |
| OBD-II | python-obd |
| CAN Bus | python-can |
| GPS | pyserial + NMEA parser |
| Server | Uvicorn (ASGI) |

---

## 📜 Automotive Standards Referenced

- **OBD-II:** SAE J1979 (diagnostic services), SAE J2012 (DTCs)
- **CAN Bus:** ISO 11898 (physical/data link layer)
- **GPS:** NMEA 0183 (sentence protocol)
- **VIN:** ISO 3779 (vehicle identification number)
- **DTC:** SAE J2012 (P, C, B, U codes)

---

## 🗺️ Roadmap

- [ ] Leaflet.js / Google Maps integration for live fleet map
- [ ] WebSocket support for real-time dashboard updates
- [ ] Driver mobile app (React Native)
- [ ] PDF report generation (daily/weekly fleet reports)
- [ ] Machine Learning-based predictive maintenance
- [ ] Multi-tenant support for fleet management SaaS
- [ ] Integration with fuel card providers
- [ ] OTA (Over-The-Air) firmware updates for telematics devices
- [ ] REST API authentication (JWT/OAuth2)
- [ ] Docker & Kubernetes deployment support

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ for the Automotive Industry<br>
  <strong>Fleet Management System</strong> — Real-time Telematics for Smarter Fleets
</p>
