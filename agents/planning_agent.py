import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====================================================
# 🌦️ WEATHER / STORM THRESHOLDS
# ====================================================
PREEMPTIVE_RAIN_THRESHOLD = 70
PREEMPTIVE_TIME_HOURS = 3

RECOVERY_RAIN_THRESHOLD = 30
RECOVERY_STABLE_CYCLES = 2

# ====================================================
# 🔆 SOLAR / SENSOR THRESHOLDS (NORMALIZED % + mW)
# ====================================================
DAYTIME_MIN_VOLTAGE = 2.5        # below this → ignore LDR
ROTATE_LDR_THRESHOLD = 15        # % → mild misalignment
SEVERE_LDR_THRESHOLD = 30        # % → strong misalignment

LOW_POWER_THRESHOLD = 0.002      # 🔥 2 mW (CRITICAL FIX)

# ====================================================
# 🧠 PLANNING AGENT
# ====================================================
def planning_agent(state: dict) -> dict:
    """
    FINAL Planning Agent

    ✔ Deterministic motor behavior
    ✔ No oscillation
    ✔ LLM used only when safe
    ✔ Always outputs planning_proposal
    """

    # ====================================================
    # 🔁 EXPLANATION CYCLE (SAFE)
    # ====================================================
    state["explain_cycle"] = state.get("explain_cycle", 0) + 1

    explanation_styles = [
        "Explain concisely.",
        "Explain with reference to power trend.",
        "Explain focusing on efficiency and motor wear.",
        "Explain in monitoring-system style.",
        "Explain with reference to past experience."
    ]

    style_instruction = explanation_styles[
        state["explain_cycle"] % len(explanation_styles)
    ]

    # ====================================================
    # 0️⃣ SAFETY OVERRIDE (ABSOLUTE)
    # ====================================================
    if state.get("safety_override"):
        reason = "Safety override active. Hardware protection takes priority."

        state.update({
            "decision": "PARK_PANEL",
            "decision_reason": reason,
            "last_action": "PARK_PANEL",
            "planning_proposal": {
                "source": "planning",
                "action": "PARK_PANEL",
                "priority": 50,
                "reason": reason,
            }
        })
        return state

    # ====================================================
    # 1️⃣ NIGHT MODE
    # ====================================================
    if state.get("is_night"):
        reason = "Night detected. Solar tracking suspended to conserve energy."

        state.update({
            "decision": "PARK_PANEL",
            "decision_reason": reason,
            "last_action": "PARK_PANEL",
            "planning_proposal": {
                "source": "planning",
                "action": "PARK_PANEL",
                "priority": 50,
                "reason": reason,
            }
        })
        return state

    # ====================================================
    # 2️⃣ CONTEXT
    # ====================================================
    forecast = state.get("forecast", {})
    rain_prob = forecast.get("rain_probability", 0)
    cloud_trend = forecast.get("cloud_trend", "unknown")
    next_hours = forecast.get("next_hours", 0)

    voltage = state.get("voltage", 0)
    power = state.get("power", 0)
    power_trend = state.get("power_trend", "unknown")

    storm_parked = state.get("storm_parked", False)

    # ====================================================
    # 🔆 LDR NORMALIZATION (0–100 %)
    # ====================================================
    ldr_diff = abs(state.get("ldr_diff", 0))

    # Ignore LDR when panel is not energized
    if voltage < DAYTIME_MIN_VOLTAGE:
        ldr_diff = 0

    # ====================================================
    # 3️⃣ LDR-BASED ALIGNMENT (DEADBAND LOGIC)
    # ====================================================
    # --- Severe misalignment: rotate immediately ---
    if ldr_diff >= SEVERE_LDR_THRESHOLD:
        reason = f"Severe LDR imbalance ({ldr_diff}%) indicates misalignment."

        state.update({
            "decision": "ROTATE_TOWARDS_LIGHT",
            "decision_reason": reason,
            "last_action": "ROTATE_TOWARDS_LIGHT",
            "planning_proposal": {
                "source": "planning",
                "action": "ROTATE_TOWARDS_LIGHT",
                "priority": 65,
                "reason": reason,
            }
        })
        return state

    # --- Moderate misalignment + low power ---
    if (
        ldr_diff >= ROTATE_LDR_THRESHOLD
        and power <= LOW_POWER_THRESHOLD
    ):
        reason = (
            f"LDR imbalance ({ldr_diff}%) with low power "
            f"({power:.4f} W) indicates misalignment."
        )

        state.update({
            "decision": "ROTATE_TOWARDS_LIGHT",
            "decision_reason": reason,
            "last_action": "ROTATE_TOWARDS_LIGHT",
            "planning_proposal": {
                "source": "planning",
                "action": "ROTATE_TOWARDS_LIGHT",
                "priority": 55,
                "reason": reason,
            }
        })
        return state

    # ====================================================
    # 4️⃣ PRE-EMPTIVE STORM PARKING
    # ====================================================
    preemptive_storm = (
        rain_prob >= PREEMPTIVE_RAIN_THRESHOLD
        and next_hours <= PREEMPTIVE_TIME_HOURS
        and cloud_trend in ["increasing", "stable"]
        and power_trend in ["falling", "stable"]
        and voltage > DAYTIME_MIN_VOLTAGE
    )

    if preemptive_storm:
        reason = (
            f"Pre-emptive parking due to {rain_prob}% rain probability "
            f"within {next_hours} hours."
        )

        state.update({
            "decision": "PARK_PANEL",
            "decision_reason": reason,
            "last_action": "PARK_PANEL",
            "storm_parked": True,
            "storm_stable_cycles": 0,
            "planning_proposal": {
                "source": "planning",
                "action": "PARK_PANEL",
                "priority": 50,
                "reason": reason,
            }
        })
        return state

    # ====================================================
    # 5️⃣ STORM RECOVERY
    # ====================================================
    if storm_parked:
        recovery_ok = (
            rain_prob <= RECOVERY_RAIN_THRESHOLD
            and cloud_trend in ["stable", "decreasing"]
            and voltage > DAYTIME_MIN_VOLTAGE
        )

        state["storm_stable_cycles"] = (
            state.get("storm_stable_cycles", 0) + 1 if recovery_ok else 0
        )

        if state["storm_stable_cycles"] >= RECOVERY_STABLE_CYCLES:
            reason = "Weather stabilized. Resuming solar alignment."

            state.update({
                "decision": "ROTATE_TOWARDS_LIGHT",
                "decision_reason": reason,
                "last_action": "ROTATE_TOWARDS_LIGHT",
                "storm_parked": False,
                "storm_stable_cycles": 0,
                "planning_proposal": {
                    "source": "planning",
                    "action": "ROTATE_TOWARDS_LIGHT",
                    "priority": 50,
                    "reason": reason,
                }
            })
            return state

        reason = "Waiting for consistent weather stability before resuming motion."

        state.update({
            "decision": "HOLD_POSITION",
            "decision_reason": reason,
            "last_action": "HOLD_POSITION",
            "planning_proposal": {
                "source": "planning",
                "action": "HOLD_POSITION",
                "priority": 50,
                "reason": reason,
            }
        })
        return state

    # ====================================================
    # 6️⃣ NORMAL DAYTIME (LLM ADVISOR – LOW FREQUENCY)
    # ====================================================
    prompt = f"""
You are an autonomous solar tracking AI.

Current state:
- LDR imbalance: {ldr_diff} %
- Voltage: {voltage} V
- Current: {state.get("current")} A
- Power: {power} W
- Power trend: {power_trend}
- Weather: {state.get("weather_risk")}

Forecast:
- Rain probability: {rain_prob}%
- Cloud trend: {cloud_trend}

Past experience:
{state.get("rag_context", "No memory.")}

Instruction:
{style_instruction}

Rules:
- Avoid unnecessary movement
- Do not park unless justified
- Prefer actions that improved power previously

Actions:
- ROTATE_TOWARDS_LIGHT
- HOLD_POSITION
- PARK_PANEL

Respond ONLY in JSON:
{{"action":"...","reason":"..."}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        result = json.loads(response.choices[0].message.content)

        state["decision"] = result["action"]
        state["decision_reason"] = result["reason"]
        state["last_action"] = result["action"]

    except Exception as e:
        state["decision"] = "HOLD_POSITION"
        state["decision_reason"] = f"Fallback due to LLM error: {e}"
        state["last_action"] = "HOLD_POSITION"

    # ====================================================
    # ✅ ALWAYS PRODUCE PLANNING PROPOSAL
    # ====================================================
    state["planning_proposal"] = {
        "source": "planning",
        "action": state["decision"],
        "priority": 50,
        "reason": state["decision_reason"],
    }

    return state
