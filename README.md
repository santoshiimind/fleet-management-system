# 🚗 Fleet Management System — Automotive Telematics

A comprehensive **Python-based fleet management platform** with real-time vehicle telematics, designed for the automotive sector.

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
