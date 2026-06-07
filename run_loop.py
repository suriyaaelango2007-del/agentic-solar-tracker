import time
import signal
import sys
import os
from datetime import datetime

# =====================================================
# 🔧 ENSURE PROJECT ROOT IN PYTHON PATH
# =====================================================
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

# =====================================================
# 📦 IMPORTS
# =====================================================
from graph.graph import build_graph
from dashboard.state_store import update_state
from dashboard.sensor_cache import get_sensor_cache
from dashboard.power_logger import log_power
from analytics.sensor_analytics import analyze_sensor_cache

# =====================================================
# 🛑 GRACEFUL SHUTDOWN
# =====================================================
running = True

def shutdown_handler(sig, frame):
    global running
    print("\n🛑 Shutting down autonomous solar tracker safely...")
    running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# =====================================================
# 🧠 BUILD GRAPH
# =====================================================
solar_graph = build_graph()

# =====================================================
# 🌞 INITIAL SYSTEM STATE
# =====================================================
state = {
    "ldr_diff": 0,
    "ldr_raw": 0,
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0,
    "power_raw": 0.0,
    "power_trend": "unknown",

    # 🔥 IMPORTANT — angles must exist
    "azimuth": 90.0,
    "elevation": 45.0,

    "weather_risk": "unknown",
    "cloud_coverage": 0,

    "last_action": "INIT",
    "decision": "HOLD_POSITION",
    "decision_reason": "System initialized.",

    "safety_faults": [],
    "safety_override": False,
    "fault_severity": "NONE",
    "fault_active": False,
    "fault_recovered": False,
    "ineffective_count": 0,

    "forecast": {},
    "storm_parked": False,
    "storm_stable_cycles": 0,

    "is_night": False,
    "night_mode": False,
    "sun_phase": "day",

    "timestamp": datetime.now().isoformat(),
    "status": "NORMAL",
}

# =====================================================
# ⏱ LOOP CONFIG
# =====================================================
CYCLE_INTERVAL = 5

print("🚀 Agentic AI Solar Tracker Started\n")

# =====================================================
# 🔁 MAIN LOOP
# =====================================================
while running:
    try:
        print("\n🔄 New control cycle")

        # =====================================================
        # 📡 SENSOR CACHE
        # =====================================================
        cache = get_sensor_cache()

        if not cache:
            print("⚠ No sensor data yet. Waiting for ESP32...")
            time.sleep(CYCLE_INTERVAL)
            continue

        summary = analyze_sensor_cache(cache)
        last_sample = cache[-1]

        raw_ldr = int(last_sample.get("ldr_diff", 0))
        raw_power = float(last_sample.get("power", 0.0))
        voltage = float(last_sample.get("voltage", 0.0))
        current = float(last_sample.get("current", 0.0))

        state.update({
            "ldr_raw": raw_ldr,
            "power_raw": raw_power,
            "ldr_diff": summary.get("ldr_avg", 0),
            "power": summary.get("power_avg", 0.0),
            "power_trend": summary.get("power_trend", "unknown"),
            "voltage": voltage,
            "current": current,
        })

        # =====================================================
        # 🧠 RUN AI GRAPH
        # =====================================================
        ai_output = solar_graph.invoke(state)

        print("🧠 AI OUTPUT:", ai_output)

        if isinstance(ai_output, dict):
            state.update(ai_output)

        # 🔥 GUARANTEE angles are preserved
        if "azimuth" not in state:
            state["azimuth"] = 90.0
        if "elevation" not in state:
            state["elevation"] = 45.0

        print(
            f"📡 Committing angles → "
            f"AZ={state.get('azimuth')} | "
            f"EL={state.get('elevation')}"
        )

        # =====================================================
        # 🕒 TIMESTAMP
        # =====================================================
        state["timestamp"] = datetime.now().isoformat()

        # =====================================================
        # 📊 LOG POWER
        # =====================================================
        log_power(state.get("power", 0.0))

        # =====================================================
        # 📊 DASHBOARD COMMIT
        # =====================================================
        print("FINAL STATE BEFORE DASHBOARD:")
        print("is_night =", state.get("is_night"))
        print("sun_phase =", state.get("sun_phase"))
        print("decision =", state.get("decision"))
        update_state(state)

        # =====================================================
        # 🖥️ CONSOLE OUTPUT
        # =====================================================
        print(
            f"🧠 Decision: {state.get('decision')} | "
            f"Reason: {state.get('decision_reason')}"
        )

        print(
            f"🔆 LDR raw: {state.get('ldr_raw')}% | "
            f"LDR avg: {state.get('ldr_diff')}% | "
            f"⚡ Power raw: {state.get('power_raw')} W | "
            f"Power avg: {state.get('power')} W | "
            f"Trend: {state.get('power_trend')}"
        )

        time.sleep(CYCLE_INTERVAL)

    except KeyboardInterrupt:
        shutdown_handler(None, None)

    except Exception as e:
        print("❌ Runtime error:", e)
        time.sleep(5)

print("✅ System stopped cleanly")
sys.exit(0)