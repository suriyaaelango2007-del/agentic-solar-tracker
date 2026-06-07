from rag.vector_store import query_memory


def rag_agent(state: dict) -> dict:
    """
    Retrieves similar past experiences
    """

    query = f"""
    LDR diff: {state['ldr_diff']}
    Weather: {state['weather_risk']}
    Power trend: {state['power_trend']}
    """

    memories = query_memory(query)

    if memories:
        context = "\n".join(
            f"- Action: {m['action']}, Outcome: {m['outcome']}"
            for m in memories
        )
    else:
        context = "No similar past memory found."

    state["rag_context"] = context
    print("[RAG] Retrieved memories:", memories)

    return state

