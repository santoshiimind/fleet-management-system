"""
DTC Analyzer — Diagnostic Trouble Code analysis engine.

Decodes OBD-II DTCs, assesses severity, and recommends actions.
Supports standard SAE J2012 codes (P, C, B, U prefix codes).
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# DTC Database — Common automotive diagnostic trouble codes
DTC_DATABASE = {
    # ── Powertrain (P) Codes ────────────────────────────────────
    # Fuel and Air Metering
    "P0100": {"desc": "Mass Air Flow (MAF) Circuit Malfunction", "severity": "high", "system": "fuel"},
    "P0101": {"desc": "MAF Sensor Range/Performance", "severity": "medium", "system": "fuel"},
    "P0102": {"desc": "MAF Sensor Circuit Low Input", "severity": "medium", "system": "fuel"},
    "P0110": {"desc": "Intake Air Temperature Sensor Malfunction", "severity": "medium", "system": "fuel"},
    "P0120": {"desc": "Throttle Position Sensor Malfunction", "severity": "high", "system": "fuel"},
    "P0130": {"desc": "O2 Sensor Circuit Malfunction (Bank 1)", "severity": "medium", "system": "emissions"},
    "P0171": {"desc": "System Too Lean (Bank 1)", "severity": "medium", "system": "fuel"},
    "P0172": {"desc": "System Too Rich (Bank 1)", "severity": "medium", "system": "fuel"},

    # Ignition System
    "P0300": {"desc": "Random/Multiple Cylinder Misfire Detected", "severity": "high", "system": "ignition"},
    "P0301": {"desc": "Cylinder 1 Misfire Detected", "severity": "high", "system": "ignition"},
    "P0302": {"desc": "Cylinder 2 Misfire Detected", "severity": "high", "system": "ignition"},
    "P0303": {"desc": "Cylinder 3 Misfire Detected", "severity": "high", "system": "ignition"},
    "P0304": {"desc": "Cylinder 4 Misfire Detected", "severity": "high", "system": "ignition"},
    "P0335": {"desc": "Crankshaft Position Sensor Malfunction", "severity": "critical", "system": "ignition"},
    "P0340": {"desc": "Camshaft Position Sensor Malfunction", "severity": "critical", "system": "ignition"},

    # Emission Controls
    "P0400": {"desc": "EGR Flow Malfunction", "severity": "medium", "system": "emissions"},
    "P0420": {"desc": "Catalyst Efficiency Below Threshold (Bank 1)", "severity": "medium", "system": "emissions"},
    "P0440": {"desc": "EVAP System Malfunction", "severity": "low", "system": "emissions"},
    "P0442": {"desc": "EVAP System Small Leak Detected", "severity": "low", "system": "emissions"},
    "P0455": {"desc": "EVAP System Large Leak Detected", "severity": "medium", "system": "emissions"},

    # Speed/Idle Control
    "P0500": {"desc": "Vehicle Speed Sensor Malfunction", "severity": "high", "system": "drivetrain"},
    "P0505": {"desc": "Idle Air Control System Malfunction", "severity": "medium", "system": "fuel"},

    # Transmission
    "P0700": {"desc": "Transmission Control System Malfunction", "severity": "high", "system": "transmission"},
    "P0715": {"desc": "Input/Turbine Speed Sensor Malfunction", "severity": "high", "system": "transmission"},
    "P0730": {"desc": "Incorrect Gear Ratio", "severity": "high", "system": "transmission"},

    # Engine Temperature
    "P0115": {"desc": "Engine Coolant Temperature Sensor Malfunction", "severity": "high", "system": "cooling"},
    "P0116": {"desc": "Coolant Temp Sensor Range/Performance", "severity": "medium", "system": "cooling"},
    "P0117": {"desc": "Coolant Temp Sensor Circuit Low", "severity": "medium", "system": "cooling"},
    "P0125": {"desc": "Insufficient Coolant Temperature for Fuel Control", "severity": "medium", "system": "cooling"},
    "P0128": {"desc": "Coolant Thermostat Below Operating Temperature", "severity": "low", "system": "cooling"},

    # ── Chassis (C) Codes ───────────────────────────────────────
    "C0035": {"desc": "Left Front Wheel Speed Sensor Circuit", "severity": "high", "system": "abs"},
    "C0040": {"desc": "Right Front Wheel Speed Sensor Circuit", "severity": "high", "system": "abs"},
    "C0050": {"desc": "Steering Assist Control Module", "severity": "critical", "system": "steering"},

    # ── Body (B) Codes ──────────────────────────────────────────
    "B0001": {"desc": "Driver Frontal Stage 1 Deployment Control", "severity": "critical", "system": "airbag"},
    "B0028": {"desc": "Airbag Warning Lamp Circuit", "severity": "high", "system": "airbag"},
    "B0100": {"desc": "Electronic Frontal Sensor 1", "severity": "critical", "system": "airbag"},

    # ── Network (U) Codes ───────────────────────────────────────
    "U0001": {"desc": "High Speed CAN Communication Bus", "severity": "high", "system": "network"},
    "U0100": {"desc": "Lost Communication with ECM/PCM", "severity": "critical", "system": "network"},
    "U0121": {"desc": "Lost Communication with ABS", "severity": "critical", "system": "network"},
    "U0140": {"desc": "Lost Communication with BCM", "severity": "high", "system": "network"},
}

SEVERITY_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}

RECOMMENDED_ACTIONS = {
    "critical": "⛔ STOP VEHICLE IMMEDIATELY. Do not drive. Tow to nearest service center.",
    "high": "⚠️ Schedule service ASAP. Avoid long trips until repaired.",
    "medium": "🔧 Service recommended within 1-2 weeks. Monitor closely.",
    "low": "ℹ️ Minor issue. Schedule during next routine service.",
}


class DTCAnalyzer:
    """
    Analyzes Diagnostic Trouble Codes and provides actionable insights.

    Automotive Context:
    ──────────────────
    DTCs are stored in the vehicle's ECU when a fault is detected.
    The MIL (Malfunction Indicator Light / Check Engine Light) illuminates
    when certain DTCs are set. Codes follow SAE J2012 standard.

    Code Structure:
    - 1st char: System (P=Powertrain, C=Chassis, B=Body, U=Network)
    - 2nd char: 0=SAE standard, 1=Manufacturer-specific
    - 3rd char: Subsystem (0-9)
    - 4th-5th: Specific fault (00-99)
    """

    def __init__(self, custom_db: Optional[Dict] = None):
        self.dtc_db = {**DTC_DATABASE, **(custom_db or {})}

    def analyze(self, dtc_codes: List[str]) -> Dict:
        """
        Analyze a list of DTC codes and return detailed diagnosis.

        Returns:
            {
                "total_codes": int,
                "max_severity": str,
                "overall_action": str,
                "safe_to_drive": bool,
                "codes": [{ code, description, severity, system, action }],
                "affected_systems": [str],
            }
        """
        if not dtc_codes:
            return {
                "total_codes": 0,
                "max_severity": "none",
                "overall_action": "No faults detected. Vehicle systems normal.",
                "safe_to_drive": True,
                "codes": [],
                "affected_systems": [],
            }

        analyzed = []
        max_severity_level = 0
        affected_systems = set()

        for code in dtc_codes:
            code = code.upper().strip()
            info = self.dtc_db.get(code)

            if info:
                severity = info["severity"]
                analyzed.append({
                    "code": code,
                    "description": info["desc"],
                    "severity": severity,
                    "system": info["system"],
                    "action": RECOMMENDED_ACTIONS[severity],
                })
                max_severity_level = max(max_severity_level, SEVERITY_PRIORITY[severity])
                affected_systems.add(info["system"])
            else:
                # Unknown code — decode from structure
                decoded = self._decode_unknown(code)
                analyzed.append({
                    "code": code,
                    "description": decoded["description"],
                    "severity": "medium",
                    "system": decoded["system"],
                    "action": RECOMMENDED_ACTIONS["medium"],
                })
                affected_systems.add(decoded["system"])

        # Determine overall status
        severity_names = {v: k for k, v in SEVERITY_PRIORITY.items()}
        max_severity = severity_names.get(max_severity_level, "low")
        safe_to_drive = max_severity_level < SEVERITY_PRIORITY["critical"]

        return {
            "total_codes": len(dtc_codes),
            "max_severity": max_severity,
            "overall_action": RECOMMENDED_ACTIONS.get(max_severity, "Monitor vehicle."),
            "safe_to_drive": safe_to_drive,
            "codes": analyzed,
            "affected_systems": sorted(affected_systems),
        }

    def _decode_unknown(self, code: str) -> Dict:
        """Decode basic info from an unknown DTC based on its structure."""
        system_map = {"P": "powertrain", "C": "chassis", "B": "body", "U": "network"}
        subsystem_map = {
            "0": "fuel_and_air", "1": "fuel_and_air", "2": "fuel_and_air",
            "3": "ignition", "4": "emissions", "5": "speed_idle",
            "6": "computer", "7": "transmission", "8": "transmission",
        }

        system = system_map.get(code[0], "unknown") if len(code) > 0 else "unknown"
        subsystem = ""
        if len(code) >= 3 and code[0] == "P":
            subsystem = subsystem_map.get(code[2], "")

        return {
            "description": f"Unknown {system} code (manufacturer-specific)",
            "system": subsystem or system,
        }

    def get_maintenance_suggestions(self, dtc_codes: List[str]) -> List[Dict]:
        """Generate maintenance suggestions based on detected DTCs."""
        analysis = self.analyze(dtc_codes)
        suggestions = []

        for code_info in analysis["codes"]:
            system = code_info["system"]

            if system in ("ignition", "fuel"):
                suggestions.append({
                    "type": "engine_diagnostic",
                    "priority": code_info["severity"],
                    "description": f"Engine diagnostic needed: {code_info['description']}",
                    "estimated_cost": "$100-300",
                })
            elif system == "transmission":
                suggestions.append({
                    "type": "transmission_service",
                    "priority": code_info["severity"],
                    "description": f"Transmission inspection: {code_info['description']}",
                    "estimated_cost": "$150-500",
                })
            elif system == "emissions":
                suggestions.append({
                    "type": "emissions_service",
                    "priority": code_info["severity"],
                    "description": f"Emissions system service: {code_info['description']}",
                    "estimated_cost": "$100-400",
                })
            elif system in ("abs", "steering"):
                suggestions.append({
                    "type": "safety_inspection",
                    "priority": "critical",
                    "description": f"Safety-critical repair: {code_info['description']}",
                    "estimated_cost": "$200-800",
                })

        return suggestions
