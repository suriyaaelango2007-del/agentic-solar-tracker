import json
import os
import time
from collections import deque

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
os.makedirs(DATA_DIR, exist_ok=True)

SENSOR_FILE = os.path.join(DATA_DIR, "sensor_cache.json")

# 🔥 5 seconds × 1Hz sampling = max 5 entries
CACHE_SECONDS = 5
MAX_SAMPLES = 5

sensor_buffer = deque(maxlen=MAX_SAMPLES)

# --------------------------------------------------

def update_sensor(data: dict):
    """
    Called by Flask API (/api/sensor)
    Adds a timestamped sensor sample
    """

    entry = {
        "timestamp": time.time(),
        "ldr_diff": int(data.get("ldr_diff", 0)),
        "voltage": float(data.get("voltage", 0)),
        "current": float(data.get("current", 0)),
        "power": float(data.get("power", 0)),
    }

    sensor_buffer.append(entry)

    # Persist buffer (for restart safety)
    with open(SENSOR_FILE, "w") as f:
        json.dump(list(sensor_buffer), f, indent=2)

# --------------------------------------------------

def get_sensor_cache():
    """
    Returns last 5 seconds of sensor samples
    Always reload from disk (process-safe)
    """

    if not os.path.exists(SENSOR_FILE):
        return []

    try:
        with open(SENSOR_FILE, "r") as f:
            data = json.load(f)

        return data[-MAX_SAMPLES:]

    except Exception:
        return []