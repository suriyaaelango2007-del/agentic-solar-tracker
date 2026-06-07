from datetime import datetime
from rag.fault_store import store_fault
from dashboard.event_logger import append_event

# ====================================================
# 🚨 FAULT SEVERITY MAP
# ====================================================
FAULT_SEVERITY = {
    "RAIN_DETECTED": "WARNING",
    "INEFFECTIVE_MOVEMENT": "INFO",
    "OVERVOLTAGE": "CRITICAL",
    "OVERCURRENT": "CRITICAL",
}

# ====================================================
# 🔧 SAFETY THRESHOLDS
# ====================================================
INEFFECTIVE_LIMIT = 5
CLOUD_IGNORE_THRESHOLD = 70

RECOVERY_CLOUD_THRESHOLD = 60
RECOVERY_LDR_THRESHOLD = 10
RECOVERY_POWER_TREND = "rising"

MAX_VOLTAGE = 20.0
MAX_CURRENT = 3.0
MIN_ACTIVE_VOLTAGE = 3.0


# ====================================================
# 🛡️ SAFETY AGENT
# ====================================================
def safety_agent(state: dict) -> dict:
    """
    Safety & fault-handling agent
    Logs only IMPORTANT events.
    """

    faults = []
    previously_active = state.get("fault_active", False)

    # ---------------- CONTEXT ----------------
    power_trend = state.get("power_trend", "unknown")
    last_action = state.get("last_action")
    cloud_coverage = state.get("cloud_coverage", 0)
    ldr_diff = abs(state.get("ldr_diff", 0))
    voltage = state.get("voltage", 0)
    current = state.get("current", 0)

    ineffective_count = state.get("ineffective_count", 0)

    # ====================================================
    # 🔍 FAULT DETECTION
    # ====================================================

    # 🌧️ Rain
    if state.get("weather_risk") == "rain":
        faults.append("RAIN_DETECTED")

    # ⚡ Electrical hard faults
    if voltage > MAX_VOLTAGE:
        faults.append("OVERVOLTAGE")

    if current > MAX_CURRENT:
        faults.append("OVERCURRENT")

    # 🔄 Ineffective movement detection
    if (
        last_action == "ROTATE_TOWARDS_LIGHT"
        and power_trend == "falling"
        and cloud_coverage < CLOUD_IGNORE_THRESHOLD
        and ldr_diff > 20
        and voltage > MIN_ACTIVE_VOLTAGE
    ):
        ineffective_count += 1
    else:
        ineffective_count = 0

    if ineffective_count >= INEFFECTIVE_LIMIT:
        faults.append("INEFFECTIVE_MOVEMENT")

    state["ineffective_count"] = ineffective_count

    # ====================================================
    # 🚨 FAULT ACTIVE → SAFETY OVERRIDE
    # ====================================================
    if faults:
        severities = [FAULT_SEVERITY[f] for f in faults]

        severity = (
            "CRITICAL" if "CRITICAL" in severities
            else "WARNING" if "WARNING" in severities
            else "INFO"
        )

        # 🔔 Log ONLY when transitioning into fault
        if not previously_active:
            for fault in faults:
                append_event(
                    FAULT_SEVERITY[fault],
                    f"{fault.replace('_', ' ').title()} detected → Panel parked"
                )

        state.update({
            "safety_faults": faults,
            "safety_override": True,
            "fault_active": True,
            "fault_recovered": False,
            "fault_severity": severity,
            "decision": "PARK_PANEL",
            "decision_reason": "Safety condition detected. Panel parked to protect hardware.",
            "status": "SAFETY",
        })

        # Store fault in memory (RAG fault DB)
        store_fault(
            f"Faults {faults}, Severity {severity}",
            {
                "faults": faults,
                "severity": severity,
                "cloud_coverage": cloud_coverage,
                "ldr_diff": ldr_diff,
                "power_trend": power_trend,
                "voltage": voltage,
                "current": current,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return state

    # ====================================================
    # 🟢 RECOVERY
    # ====================================================
    recovery_conditions = (
        cloud_coverage < RECOVERY_CLOUD_THRESHOLD
        and ldr_diff < RECOVERY_LDR_THRESHOLD
        and power_trend == RECOVERY_POWER_TREND
    )

    if previously_active and recovery_conditions:
        append_event(
            "RECOVERY",
            "Conditions improved → Safety fault cleared"
        )

        state.update({
            "fault_active": False,
            "fault_recovered": True,
            "safety_override": False,
            "safety_faults": [],
            "fault_severity": "NONE",
            "ineffective_count": 0,
            "status": "NORMAL",
        })

        return state

    # ====================================================
    # 🟦 NORMAL PASS-THROUGH
    # ====================================================
    state.update({
        "fault_active": False,
        "fault_recovered": False,
        "safety_override": False,
        "safety_faults": [],
        "fault_severity": "NONE",
        "status": "NORMAL",
    })

    return state