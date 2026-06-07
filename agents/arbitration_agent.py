def arbitration_agent(state: dict) -> dict:
    """
    Final authority for decisions.
    Night and Safety have absolute authority.
    """

    # ====================================================
    # 🔒 HARD LOCK: SAFETY
    # ====================================================
    if state.get("safety_override"):
        state.update({
            "decision": "PARK_PANEL",
            "decision_reason": "[SAFETY] Safety override active",
            "decision_source": "safety"
        })
        print("🧠 Arbitration winner: SAFETY")
        return state

    # ====================================================
    # 🌙 HARD LOCK: NIGHT MODE
    # ====================================================
    if state.get("is_night"):
        state.update({
            "decision": "PARK_PANEL",
            "decision_reason": "[NIGHT_DAY] Night mode active",
            "decision_source": "night_day"
        })
        print("🧠 Arbitration winner: NIGHT_MODE")
        return state

    proposals = []

    # ====================================================
    # 🌧 FORECAST
    # ====================================================
    forecast = state.get("forecast", {})
    if forecast.get("rain_probability", 0) >= 70:
        proposals.append({
            "source": "forecast",
            "action": "PARK_PANEL",
            "priority": 70,
            "reason": "High rain probability forecast"
        })

    # ====================================================
    # 🧠 PLANNING
    # ====================================================
    planning_proposal = state.get("planning_proposal")
    if planning_proposal:
        proposals.append(planning_proposal)

    # ====================================================
    # 📚 RAG MEMORY
    # ====================================================
    if "INEFFECTIVE" in str(state.get("rag_context", "")):
        proposals.append({
            "source": "rag",
            "action": "HOLD_POSITION",
            "priority": 30,
            "reason": "Historical ineffective movement"
        })

    # ====================================================
    # 🚨 DEFAULT
    # ====================================================
    if not proposals:
        state.update({
            "decision": "HOLD_POSITION",
            "decision_reason": "Safe default",
            "decision_source": "fallback"
        })
        return state

    proposals.sort(key=lambda x: x["priority"], reverse=True)
    winner = proposals[0]

    state["decision"] = winner["action"]
    state["decision_source"] = winner["source"]

    if winner["source"] == "planning":
        state["decision_reason"] = winner["reason"]
    else:
        state["decision_reason"] = f"[{winner['source'].upper()}] {winner['reason']}"

    print("🧠 Arbitration winner:", winner)

    return state