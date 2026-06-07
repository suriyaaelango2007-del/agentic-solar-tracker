import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data")
)
os.makedirs(DATA_DIR, exist_ok=True)

POWER_FILE = os.path.join(DATA_DIR, "power_log.json")


# 🔥 MUST MATCH run_loop.py
SAMPLE_INTERVAL_SEC = 5

def log_power(power_w: float):
    energy_kwh = (power_w * SAMPLE_INTERVAL_SEC) / (3600 * 1000)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "power": power_w,
        "energy_kwh": energy_kwh,
    }

    data = []
    if os.path.exists(POWER_FILE):
        with open(POWER_FILE, "r") as f:
            data = json.load(f)

    data.append(entry)

    with open(POWER_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --------------------------------------------------

def _safe_energy(entry: dict) -> float:
    if "energy_kwh" in entry:
        return entry["energy_kwh"]
    power = entry.get("power", 0)
    return (power * SAMPLE_INTERVAL_SEC) / (3600 * 1000)

# --------------------------------------------------

def get_energy_summary():
    if not os.path.exists(POWER_FILE):
        return {"today": 0, "week": 0, "month": 0, "lifetime": 0}

    with open(POWER_FILE, "r") as f:
        data = json.load(f)

    now = datetime.now()
    today = week = month = lifetime = 0.0

    for d in data:
        ts = datetime.fromisoformat(d["timestamp"])
        e = _safe_energy(d)

        lifetime += e
        if ts.date() == now.date():
            today += e
        if ts >= now - timedelta(days=7):
            week += e
        if ts.month == now.month and ts.year == now.year:
            month += e

    return {
        "today": round(today, 4),
        "week": round(week, 4),
        "month": round(month, 4),
        "lifetime": round(lifetime, 4),
    }

# --------------------------------------------------

def get_power_data(days: int):
    if not os.path.exists(POWER_FILE):
        return []

    cutoff = datetime.now() - timedelta(days=days)

    with open(POWER_FILE, "r") as f:
        data = json.load(f)

    return [
        {"timestamp": d["timestamp"], "power": d.get("power", 0)}
        for d in data
        if datetime.fromisoformat(d["timestamp"]) >= cutoff
    ]

# --------------------------------------------------

def get_energy_data(days: int):
    if not os.path.exists(POWER_FILE):
        return []

    cutoff = datetime.now() - timedelta(days=days)
    buckets = defaultdict(float)

    with open(POWER_FILE, "r") as f:
        data = json.load(f)

    for d in data:
        ts = datetime.fromisoformat(d["timestamp"])
        if ts < cutoff:
            continue

        if days <= 30:
            key = ts.strftime("%Y-%m-%d")
        else:
            key = ts.strftime("%Y-%m")

        buckets[key] += _safe_energy(d)

    return [
        {"period": k, "energy_kwh": round(v, 4)}
        for k, v in sorted(buckets.items())
    ]
