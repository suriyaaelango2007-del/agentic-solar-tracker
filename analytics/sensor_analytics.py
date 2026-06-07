from statistics import mean


def analyze_sensor_cache(cache: list) -> dict:
    """
    Analyze last 5 seconds of sensor data
    Provides:
        - Raw LDR
        - Averaged LDR
        - Power average
        - Power trend
        - Stability flag
    """

    if not cache:
        return {
            "ldr_raw": 0,
            "ldr_avg": 0,
            "power_raw": 0.0,
            "power_avg": 0.0,
            "power_trend": "unknown",
            "stable": True,
        }

    # ===============================
    # Extract values
    # ===============================
    ldr_values = [s.get("ldr_diff", 0) for s in cache]
    power_values = [s.get("power", 0.0) for s in cache]

    # Raw (latest sample)
    ldr_raw = ldr_values[-1]
    power_raw = power_values[-1]

    # Averaged (smoothed)
    ldr_avg = round(mean(ldr_values), 1)
    power_avg = round(mean(power_values), 6)

    # ===============================
    # Power trend detection
    # ===============================
    if len(power_values) < 2:
        power_trend = "unknown"
    elif power_values[-1] > power_values[0] * 1.1:
        power_trend = "rising"
    elif power_values[-1] < power_values[0] * 0.9:
        power_trend = "falling"
    else:
        power_trend = "stable"

    stable = power_trend == "stable"

    return {
        "ldr_raw": ldr_raw,
        "ldr_avg": ldr_avg,
        "power_raw": power_raw,
        "power_avg": power_avg,
        "power_trend": power_trend,
        "stable": stable,
    }