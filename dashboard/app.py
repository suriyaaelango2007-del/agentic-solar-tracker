import os
import sys

# 🔧 Ensure project root is in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from flask import Flask, jsonify, render_template, request

from dashboard.state_store import get_state
from dashboard.power_logger import (
    get_energy_data,
    get_power_data,
    get_energy_summary
)
from dashboard.event_logger import get_events
from dashboard.sensor_cache import update_sensor

app = Flask(__name__)


# ---------------- SENSOR INGEST (ESP32) ----------------
@app.route("/api/sensor", methods=["POST"])
def api_sensor():
    data = request.get_json(force=True)

    update_sensor({
        "ldr_diff": int(data.get("ldr_diff", 0)),
        "voltage": float(data.get("voltage", 0)),
        "current": float(data.get("current", 0)),
        "power": float(data.get("power", 0)),
    })

    return {"status": "ok"}

# ---------------- DASHBOARD ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def api_state():
    return jsonify(get_state())

@app.route("/api/power/day")
def power_day():
    return jsonify(get_power_data(1))

@app.route("/api/energy/week")
def energy_week():
    return jsonify(get_energy_data(7))

@app.route("/api/energy/month")
def energy_month():
    return jsonify(get_energy_data(30))

@app.route("/api/energy/year")
def energy_year():
    return jsonify(get_energy_data(365))

@app.route("/api/energy/summary")
def energy_summary():
    return jsonify(get_energy_summary())

@app.route("/api/events")
def api_events():
    events = get_events()

    important = [
        e for e in events
        if e["level"] in ["CRITICAL", "WARNING", "RECOVERY"]
    ]

    return jsonify(important)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
