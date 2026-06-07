from typing import TypedDict, Optional, Dict, Any, List


class SolarState(TypedDict, total=False):
    # ---------------- Sensor perception ----------------
    ldr_diff: int
    voltage: float
    current: float
    power: float
    prev_power: float

    # ---------------- Environment ----------------
    weather_risk: str          # clear / cloudy / rain
    cloud_coverage: int
    forecast: dict
    is_night: bool
    sun_phase: str
    power_trend: str           # rising / falling / stable

    # ---------------- Decision system ----------------
    decision: Optional[str]
    decision_reason: str
    decision_source: str
    last_action: Optional[str]

    # 🔥🔥🔥 THIS IS THE MISSING FIELD 🔥🔥🔥
    planning_proposal: Optional[Dict[str, Any]]

    # ---------------- Safety ----------------
    safety_override: bool
    safety_faults: List[str]
    fault_active: bool
    fault_recovered: bool
    fault_severity: str
    ineffective_count: int

    # ---------------- Memory / RAG ----------------
    rag_context: Optional[str]

    # ---------------- Panel orientation ----------------
    azimuth: float
    elevation: float

    # ---------------- Metadata ----------------
    timestamp: str
    status: str
