import os
from datetime import datetime
from rag.vector_store import add_memory
from dashboard.power_logger import log_power

INDEX_FILE = "rag/faiss.index"

def monitoring_agent(state: dict) -> dict:
    """
    Monitoring agent:
    - Computes power & trend
    - Logs energy
    - Adds RAG memory
    - PRESERVES dashboard-critical fields
    """

    # ---------- POWER COMPUTATION ----------
    prev_power = state.get("prev_power", state.get("power", 0))

    current_power = (
        state.get("power")
        if state.get("power") is not None
        else state.get("voltage", 0) * state.get("current", 0)
    )

    state["power"] = current_power
    state["prev_power"] = current_power
    state["timestamp"] = datetime.now().isoformat()

    if current_power > prev_power:
        state["power_trend"] = "rising"
        outcome = "positive"
    else:
        state["power_trend"] = "falling"
        outcome = "negative"

    # ---------- RAG MEMORY ----------
    should_store = False
    if outcome == "positive":
        should_store = True
    elif not os.path.exists(INDEX_FILE):
        should_store = True
        outcome = "exploration"

    if should_store:
        add_memory(
            f"LDR {state.get('ldr_diff', 0)} "
            f"Weather {state.get('weather_risk', 'unknown')} "
            f"Action {state.get('decision', 'HOLD_POSITION')} "
            f"Power {current_power}",
            {
                "action": state.get("decision"),
                "outcome": outcome,
                "power": current_power,
            },
        )

    # ---------- LOGGING ----------
    log_power(current_power)

    # 🔐 PRESERVE DASHBOARD FIELDS (CRITICAL)
    state.setdefault("decision", "--")
    state.setdefault("decision_reason", "")
    state.setdefault("status", "NORMAL")

    return state
