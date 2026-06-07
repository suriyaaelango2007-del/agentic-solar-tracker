from graph.graph import build_graph

if __name__ == "__main__":
    solar_graph = build_graph()

    initial_state = {
        "ldr_diff": 0,
        "voltage": 0.0,
        "current": 0.0,
        "power": 0.0,
        "azimuth": 90.0,
        "elevation": 45.0,
        "weather_risk": "clear",
        "power_trend": "stable",
        "last_action": None,
        "decision": None,
        "rag_context": None,
        "decision_reason": ""

    }

    result = solar_graph.invoke(initial_state)

    print("\n✅ FINAL STATE")
    for k, v in result.items():
        print(f"{k}: {v}")
