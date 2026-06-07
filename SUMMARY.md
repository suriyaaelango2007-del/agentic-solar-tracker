# Agentic Solar Tracker - Project Summary

Purpose: An autonomous solar tracking system that fuses sensor data, weather signals, RAG memory, and safety logic to decide panel actions and serve live status to a dashboard and ESP32 hardware.

Core flow:
1. Sensor samples arrive via `/api/sensor` or the serial bridge.
2. `run_loop.py` aggregates the last 5 seconds, runs the LangGraph pipeline, and writes a single dashboard state.
3. The ESP32 reads the latest decision from `/api/state` and drives the hardware.

Key components:
- LangGraph pipeline in `graph/graph.py` with agents for weather, night/day, forecast, RAG memory, planning, arbitration, safety, fault analytics, control, alerts, and monitoring.
- Dashboard server in `dashboard/app.py` (Flask) with JSON APIs and UI template.
- RAG memory and fault memory using FAISS in `rag/`.
- Hardware firmware sketches and protocol notes in `hardware/`.

Integrations:
- OpenWeather for live weather and short-term forecast.
- OpenAI for planning (LLM) and embeddings (RAG memory).
- Pushover for safety alerts and recovery notifications.

Primary entry points:
- `run_loop.py` for the autonomous loop.
- `dashboard/app.py` for the web dashboard and API server.
- `bridge/esp32_serial_bridge.py` for optional serial ingest.
- `app.py` for a single-step graph invocation (test harness).

Data stores:
- `data/sensor_cache.json` (5-second sensor window)
- `data/latest_state.json` (dashboard state)
- `data/power_log.json` (power/energy history)
- `data/events_log.json` (fault and recovery events)
