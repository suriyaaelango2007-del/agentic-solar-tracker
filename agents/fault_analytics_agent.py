from rag.fault_store import retrieve_faults


def fault_analytics_agent(state: dict) -> dict:
    """
    Analyzes current faults using historical fault memory
    """

    if not state.get("safety_override"):
        return state

    query = (
        f"Fault {state['safety_faults']}, "
        f"Voltage {state['voltage']}, "
        f"Weather {state['weather_risk']}"
    )

    past_faults = retrieve_faults(query)

    if not past_faults:
        state["fault_analysis"] = "No similar historical faults found."
        return state

    # Simple pattern extraction
    fault_types = [f["faults"] for f in past_faults]

    state["fault_analysis"] = (
        f"Similar faults occurred before. "
        f"Patterns observed: {fault_types}. "
        f"Possible cause: recurring electrical/environmental condition."
    )

    return state
