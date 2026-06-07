import json
import os
from datetime import datetime

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
os.makedirs(DATA_DIR, exist_ok=True)

EVENT_FILE = os.path.join(DATA_DIR, "events_log.json")



def append_event(level: str, message: str):
    """
    Append system event with FULL date + time
    """
    event = {
        # ✅ Date + Time (professional format)
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
    }

    data = []

    if os.path.exists(EVENT_FILE):
        with open(EVENT_FILE, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []

    # newest events at bottom (or change to insert(0) if you prefer)
    data.append(event)

    # keep only last 50 events
    data = data[-50:]

    with open(EVENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_events():
    if not os.path.exists(EVENT_FILE):
        return []
    with open(EVENT_FILE, "r") as f:
        return json.load(f)
