import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def forecast_agent(state: dict) -> dict:
    """
    Fetch short-term weather forecast (next ~3 hours)
    Uses POP (probability of precipitation) correctly
    """

    if not API_KEY or not LAT or not LON:
        print("⚠️ Forecast API not configured")
        return state

    try:
        response = requests.get(
            FORECAST_URL,
            params={
                "lat": LAT,
                "lon": LON,
                "appid": API_KEY,
                "units": "metric",
            },
            timeout=5,
        )

        data = response.json()

        if response.status_code != 200:
            print("⚠️ Forecast API error:", data)
            return state

        forecasts = data.get("list", [])[:3]  # next ~3 hours

        pop_values = []
        cloud_values = []
        rain_volume = 0.0

        for f in forecasts:
            # POP = probability of precipitation (0.0–1.0)
            pop_values.append(f.get("pop", 0.0))

            # Cloud percentage
            cloud_values.append(f.get("clouds", {}).get("all", 0))

            # Actual rain volume (mm)
            if "rain" in f and "3h" in f["rain"]:
                rain_volume += f["rain"]["3h"]

        # ---- Calculate rain probability correctly ----
        avg_pop = sum(pop_values) / max(len(pop_values), 1)
        rain_probability = int(avg_pop * 100)

        # ---- Cloud trend ----
        cloud_trend = "stable"
        if len(cloud_values) >= 2:
            if cloud_values[-1] > cloud_values[0] + 10:
                cloud_trend = "increasing"
            elif cloud_values[-1] < cloud_values[0] - 10:
                cloud_trend = "decreasing"

        # ---- Sanity correction ----
        # Heavy clouds but no rain volume → reduce rain probability
        if rain_volume == 0 and rain_probability > 30:
            rain_probability = min(rain_probability, 30)

        # ---- Update state ----
        state["forecast"] = {
            "rain_probability": rain_probability,
            "cloud_trend": cloud_trend,
            "next_hours": len(forecasts),
        }

        print(
            f"🔮 Forecast | Rain chance: {rain_probability}%, "
            f"Cloud trend: {cloud_trend}, "
            f"Rain volume: {rain_volume:.2f} mm"
        )

    except Exception as e:
        print("⚠️ Forecast agent exception:", e)

    return state
