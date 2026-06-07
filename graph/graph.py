from langgraph.graph import StateGraph
from graph.state import SolarState

from agents.perception_agent import perception_agent
from agents.weather_agent import weather_agent
from agents.night_day_agent import night_day_agent
from agents.forecast_agent import forecast_agent
from agents.rag_agent import rag_agent
from agents.planning_agent import planning_agent
from agents.safety_agent import safety_agent
from agents.fault_analytics_agent import fault_analytics_agent
from agents.control_agent import control_agent
from agents.alert_agent import alert_agent
from agents.arbitration_agent import arbitration_agent
from agents.monitoring_agent import monitoring_agent




def build_graph():
    graph = StateGraph(SolarState)

    # -------- Register nodes --------
    graph.add_node("perception", perception_agent)
    graph.add_node("weather", weather_agent)
    graph.add_node("forecast", forecast_agent)
    graph.add_node("rag", rag_agent)
    graph.add_node("planning", planning_agent)
    graph.add_node("night_day", night_day_agent)
    graph.add_node("safety", safety_agent)
    graph.add_node("arbitration", arbitration_agent)
    graph.add_node("fault_analytics", fault_analytics_agent)
    graph.add_node("control", control_agent)
    graph.add_node("alert", alert_agent)
    graph.add_node("monitoring", monitoring_agent)

    # -------- Entry --------
    graph.set_entry_point("perception")

    # -------- Correct execution flow --------
    graph.add_edge("perception", "weather")
    graph.add_edge("weather", "forecast")
    graph.add_edge("forecast", "rag")
    graph.add_edge("rag", "planning")

    # 🔥 CRITICAL FIX
    graph.add_edge("planning", "night_day")   # night AFTER planning
    graph.add_edge("night_day", "safety")     # safety AFTER night
    graph.add_edge("safety", "arbitration")   # arbitration LAST authority

    graph.add_edge("arbitration", "fault_analytics")
    graph.add_edge("fault_analytics", "control")
    graph.add_edge("control", "alert")
    graph.add_edge("alert", "monitoring")

    return graph.compile()