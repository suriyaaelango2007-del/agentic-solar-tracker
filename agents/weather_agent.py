import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def weather_agent(state: dict) -> dict:
    """
    Fetch real-time weather safely (NO crashes)
    """

    if not API_KEY or not LAT or not LON:
        print("⚠️ Weather API not configured properly")
        return state

    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "lat": LAT,
                "lon": LON,
                "appid": API_KEY,
                "units": "metric",
            },
            timeout=5,
        )

        data = response.json()

        # ---- Handle API error responses ----
        if response.status_code != 200:
            print("⚠️ Weather API response error:", data)
            return state

        # ---- Safe extraction ----
        sys_data = data.get("sys", {})
        clouds_data = data.get("clouds", {})
        weather_list = data.get("weather", [])

        sunrise = sys_data.get("sunrise")
        sunset = sys_data.get("sunset")
        current_time = data.get("dt")

        clouds = clouds_data.get("all", 0)

        # ---- Rain detection ----
        rain = False
        for w in weather_list:
            if "rain" in w.get("main", "").lower():
                rain = True

        # ---- Weather risk ----
        if rain:
            weather_risk = "rain"
        elif clouds > 70:
            weather_risk = "cloudy"
        else:
            weather_risk = "clear"

        # ---- Day / Night ----
        is_night = False
        if sunrise and sunset and current_time:
            is_night = not (sunrise <= current_time <= sunset)

        # ---- Update state ----
        state["weather_risk"] = weather_risk
        state["cloud_coverage"] = clouds
        state["is_night"] = is_night

        print(
            f"🌦️ Weather | Risk: {weather_risk}, "
            f"Clouds: {clouds}%, Night: {is_night}"
        )

    except Exception as e:
        print("⚠️ Weather API exception:", e)

    return state
