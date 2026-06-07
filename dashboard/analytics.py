import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POWER_LOG = os.path.join(BASE_DIR, "power_log.csv")


def read_logs():
    if not os.path.exists(POWER_LOG):
        return []
    with open(POWER_LOG, "r") as f:
        reader = csv.DictReader(f)
        return [
            (datetime.fromisoformat(r["timestamp"]), float(r["power"]))
            for r in reader
        ]


def integrate_energy(data):
    """Returns total energy in Wh"""
    energy = 0.0
    for i in range(1, len(data)):
        t1, p1 = data[i - 1]
        t2, _ = data[i]
        dt_hours = (t2 - t1).total_seconds() / 3600
        energy += p1 * dt_hours
    return round(energy, 2)


# -------- TODAY --------
def today_power_energy():
    today = datetime.now().date()
    data = [(t, p) for t, p in read_logs() if t.date() == today]
    return {
        "power": [(t.isoformat(), p) for t, p in data],
        "energy_wh": integrate_energy(data),
    }


# -------- WEEK --------
def weekly_power_energy():
    cutoff = datetime.now() - timedelta(days=7)
    buckets = defaultdict(list)

    for t, p in read_logs():
        if t >= cutoff:
            key = t.replace(minute=0, second=0, microsecond=0)
            buckets[key].append(p)

    power = [(k.isoformat(), sum(v)/len(v)) for k, v in sorted(buckets.items())]
    energy = sum(v for _, v in power) * 1  # Wh approximation


    return power, round(energy / 1000, 3)  # kWh


# -------- MONTH --------
def monthly_power_energy():
    cutoff = datetime.now() - timedelta(days=30)
    buckets = defaultdict(list)

    for t, p in read_logs():
        if t >= cutoff:
            buckets[t.date()].append(p)

    power = [(str(k), sum(v)/len(v)) for k, v in sorted(buckets.items())]
    energy = integrate_energy([(datetime.now(), v) for _, v in power])

    return power, round(energy / 1000, 3)


# -------- YEAR --------
def yearly_power_energy():
    buckets = defaultdict(list)

    for t, p in read_logs():
        buckets[t.strftime("%Y-%m")].append(p)

    power = [(k, sum(v)/len(v)) for k, v in sorted(buckets.items())]
    energy = integrate_energy([(datetime.now(), v) for _, v in power])

    return power, round(energy / 1000, 3)
