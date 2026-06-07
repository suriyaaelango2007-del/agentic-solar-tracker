import json
import os
from datetime import datetime

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
os.makedirs(DATA_DIR, exist_ok=True)

STATE_FILE = os.path.join(DATA_DIR, "latest_state.json")


DEFAULT_STATE = {
    "power": 0.0,
    "voltage": 0.0,
    "current": 0.0,
    "power_trend": "unknown",
    "azimuth": 90,
    "elevation": 45,
    "weather_risk": "unknown",
    "cloud_coverage": 0,
    "ldr_diff": 0,

    "fault_active": False,
    "fault_severity": "NONE",
    "safety_override": False,

    "is_night": False,
    "sun_phase": "day",

    "decision": "--",
    "decision_reason": "",

    "status": "NORMAL",
    "timestamp": None,
}

def update_state(state: dict):
    """
    FINAL dashboard commit point.
    NOTHING after this should change dashboard-visible fields.
    """

    merged = DEFAULT_STATE.copy()
    merged.update(state)

    # 🔒 HARD PRESERVE ENVIRONMENT FIELDS
    merged["weather_risk"] = state.get("weather_risk", merged["weather_risk"])
    merged["cloud_coverage"] = state.get("cloud_coverage", merged["cloud_coverage"])
    merged["ldr_diff"] = state.get("ldr_diff", merged["ldr_diff"])


    # ---------------- HARD GUARANTEES ----------------
    merged["decision"] = state.get("decision") or "--"
    merged["decision_reason"] = state.get("decision_reason") or ""

    merged["fault_active"] = bool(state.get("fault_active", False))
    merged["fault_severity"] = state.get("fault_severity", "NONE")
    merged["is_night"] = bool(state.get("is_night", False))

    # ---------------- STATUS (SINGLE SOURCE) ----------------
    if merged["fault_active"]:
        merged["status"] = f"SAFETY ({merged['fault_severity']})"
    elif merged["is_night"]:
        merged["status"] = "SLEEP (NIGHT)"
    else:
        merged["status"] = "NORMAL"

    merged["timestamp"] = state.get("timestamp") or datetime.now().isoformat()

    with open(STATE_FILE, "w") as f:
        json.dump(merged, f, indent=2)

def get_state():
    if not os.path.exists(STATE_FILE):
        return DEFAULT_STATE.copy()

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return DEFAULT_STATE.copy()

    merged = DEFAULT_STATE.copy()
    merged.update(data)

    # 🔐 ABSOLUTE SAFETY
    if merged.get("fault_active"):
        merged["status"] = f"SAFETY ({merged.get('fault_severity', 'NONE')})"
    elif merged.get("is_night"):
        merged["status"] = "SLEEP (NIGHT)"
    else:
        merged["status"] = "NORMAL"

    return merged
