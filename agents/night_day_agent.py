def night_day_agent(state: dict) -> dict:
    """
    Stable night detection calibrated for real sensor noise.
    """

    ldr_diff = state.get("ldr_diff", 0)
    power = state.get("power", 0)
    voltage = state.get("voltage", 0)

    prev_night = state.get("night_mode", False)

    # -------- Calibrated Thresholds --------
    NIGHT_LDR = 10
    DAY_LDR = 35

    NIGHT_POWER = 0.00005     # 🔥 increased from 0.00025
    DAY_POWER = 0.001       # strong sunrise threshold

    # -------- Sensor Conditions --------
    sensor_night = (
        ldr_diff < NIGHT_LDR
        and power < NIGHT_POWER
        and voltage < 1.2
    )

    sensor_day = (
        ldr_diff > DAY_LDR
        and power > DAY_POWER
        and voltage > 2.0
    )

    # -------- Hysteresis --------
    if prev_night:
        is_night = not sensor_day
    else:
        is_night = sensor_night

    state["is_night"] = is_night
    state["night_mode"] = is_night
    state["sun_phase"] = "night" if is_night else "day"

    return state