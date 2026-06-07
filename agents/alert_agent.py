import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

LAST_ALERT = {"faults": None, "time": 0}

ALERT_COOLDOWN = {
    "INFO": 900,
    "WARNING": 300,
    "CRITICAL": 30,
}

PUSHOVER_PRIORITY = {
    "INFO": -1,
    "WARNING": 0,
    "CRITICAL": 1,
}


def send_pushover(message: str, priority: int):
    requests.post(
        PUSHOVER_URL,
        data={
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
            "priority": priority,
        },
        timeout=5,
    )


def alert_agent(state: dict) -> dict:
    now = time.time()

    # -------- FAULT ALERT --------
    if state.get("safety_override"):
        faults = state.get("safety_faults", [])
        severity = state.get("fault_severity", "INFO")
        cooldown = ALERT_COOLDOWN.get(severity, 300)

        if LAST_ALERT["faults"] != faults or now - LAST_ALERT["time"] > cooldown:
            LAST_ALERT["faults"] = faults
            LAST_ALERT["time"] = now

            send_pushover(
                f"🚨 SOLAR TRACKER ALERT ({severity})\n\n"
                f"Faults: {faults}\n"
                f"Action: {state['decision']}\n"
                f"Voltage: {state['voltage']} V\n"
                f"Current: {state['current']} A",
                PUSHOVER_PRIORITY[severity],
            )

    # -------- RECOVERY ALERT --------
    if state.get("fault_recovered"):
        send_pushover(
            "🟢 SOLAR TRACKER RECOVERED\n\n"
            "Conditions normalized.\n"
            "Tracking resumed safely.",
            0,
        )

    return state
