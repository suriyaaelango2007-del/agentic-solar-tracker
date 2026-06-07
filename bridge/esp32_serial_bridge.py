import sys
import os
import json
import time
import serial

# -------------------------------------------------
# 🔧 Fix import path (project root visibility)
# -------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

# -------------------------------------------------
# 🧠 SENSOR CACHE (ONLY PLACE WE WRITE)
# -------------------------------------------------
from dashboard.sensor_cache import update_sensor

# -------------------------------------------------
# 🔌 SERIAL CONFIG
# -------------------------------------------------
PORT = "COM7"        # 🔁 change if needed
BAUD = 115200
READ_TIMEOUT = 2

# -------------------------------------------------
# 🧠 EXPECTED ESP32 JSON FORMAT
# {"voltage":17.82,"current":1.61,"power":28.7}
# -------------------------------------------------

def main():
    print("🔌 Starting ESP32 Serial Bridge...")

    try:
        ser = serial.Serial(PORT, BAUD, timeout=READ_TIMEOUT)
        time.sleep(2)  # 🔥 ESP32 reset delay
        print(f"✅ Connected to ESP32 on {PORT}")
    except serial.SerialException as e:
        print("❌ Serial open failed:", e)
        return

    while True:
        try:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            # ✅ Ignore ESP32 bootloader noise
            if not line.startswith("{"):
                print("⚠️ Non-JSON (boot/log), ignored:", line)
                continue

            print("📡 RAW JSON:", line)

            # ---------- Parse JSON ----------
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print("⚠️ JSON parse failed, skipping")
                continue

            # ---------- Validate ----------
            try:
                voltage = float(data.get("voltage", 0.0))
                current = float(data.get("current", 0.0))
                power = float(data.get("power", voltage * current))
            except (ValueError, TypeError):
                print("⚠️ Invalid numeric data, skipping")
                continue

            # ---------- Update sensor cache ----------
            update_sensor({
                "voltage": round(voltage, 2),
                "current": round(current, 3),
                "power": round(power, 2),
            })

            print(
                f"📥 Sensor cached | "
                f"V={voltage:.2f}V "
                f"I={current:.3f}A "
                f"P={power:.2f}W"
            )

        except KeyboardInterrupt:
            print("\n🛑 ESP32 bridge stopped by user")
            break

        except Exception as e:
            print("❌ ESP32 bridge runtime error:", e)
        time.sleep(1)


    ser.close()
    print("✅ Serial closed cleanly")

if __name__ == "__main__":
    main()
