def control_agent(state: dict) -> dict:
    """
    ADVANCED CONTROL AGENT – Dual Axis Intelligent Version

    Responsibilities:
    - Compute azimuth & elevation angles
    - Apply incremental smooth movement
    - Enforce mechanical limits
    - Handle night & storm parking
    - Respect safety override
    - Publish final angles to ESP32
    """

    # =====================================================
    # 🔒 Mechanical Limits
    # =====================================================
    AZ_MIN, AZ_MAX = 0, 180
    EL_MIN, EL_MAX = 0, 90

    AZ_STEP = 3
    EL_STEP = 2

    # Storm / Night parking angles
    PARK_AZIMUTH = 0
    PARK_ELEVATION = 0

    # =====================================================
    # 📌 Get current angles (safe defaults)
    # =====================================================
    az = state.get("azimuth", 90.0)
    el = state.get("elevation", 45.0)

    decision = state.get("decision", "HOLD_POSITION")

    # =====================================================
    # 🚨 SAFETY OVERRIDE (ABSOLUTE PRIORITY)
    # =====================================================
    if state.get("safety_override"):
        az = PARK_AZIMUTH
        el = PARK_ELEVATION

        state.update({
            "azimuth": az,
            "elevation": el,
            "last_action": "PARK_PANEL"
        })

        print("🛑 SAFETY OVERRIDE → Panel parked")
        return state

    # =====================================================
    # 🌙 NIGHT MODE PARKING
    # =====================================================
    if state.get("is_night"):
        az = PARK_AZIMUTH
        el = PARK_ELEVATION

        state.update({
            "azimuth": az,
            "elevation": el,
            "last_action": "PARK_PANEL"
        })

        print("🌙 Night mode → Panel parked")
        return state

    # =====================================================
    # 🎯 DECISION EXECUTION
    # =====================================================
    if decision == "ROTATE_TOWARDS_LIGHT":

        # Increment angles gradually
        az += AZ_STEP
        el += EL_STEP

        state["last_action"] = "ROTATE_TOWARDS_LIGHT"

    elif decision == "PARK_PANEL":

        az = PARK_AZIMUTH
        el = PARK_ELEVATION

        state["last_action"] = "PARK_PANEL"

    elif decision == "HOLD_POSITION":

        state["last_action"] = "HOLD_POSITION"

    else:
        print("⚠ Unknown decision → Holding")
        state["last_action"] = "HOLD_POSITION"

    # =====================================================
    # 🔐 CLAMP LIMITS (CRITICAL SAFETY)
    # =====================================================
    az = max(AZ_MIN, min(AZ_MAX, az))
    el = max(EL_MIN, min(EL_MAX, el))

    # =====================================================
    # 📤 Publish updated angles
    # =====================================================
    state.update({
        "azimuth": round(az, 2),
        "elevation": round(el, 2)
    })

    print(
        f"[CONTROL] Decision: {decision} | "
        f"Azimuth: {az} | Elevation: {el}"
    )

    return state