#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// ---------------- WIFI ----------------
const char* ssid = "SolarAI";
const char* password = "solar1234";

// ---------------- SERVER ----------------
const char* sensorUrl   = "http://10.149.101.48:5000/api/sensor";
const char* decisionUrl = "http://10.149.101.48:5000/api/state";

// ---------------- UART ----------------
HardwareSerial ArduinoSerial(2); // RX=16 TX=17

// ---------------- INA219 ----------------
Adafruit_INA219 ina219;

// ---------------- LDR PINS (ESP32 ADC) ----------------
#define LDR1 32
#define LDR2 33
#define LDR3 34
#define LDR4 35

// ---------------- LDR NORMALIZATION ----------------
// Practical️ Realistic max imbalance (NOT ADC max)
#define LDR_MAX_DIFF 1600.0

void setup() {
  Serial.begin(115200);
  ArduinoSerial.begin(9600, SERIAL_8N1, 16, 17);

  Wire.begin(21, 19);

  if (!ina219.begin()) {
    Serial.println("❌ INA219 not found");
    while (1);
  }
  ina219.setCalibration_16V_400mA();

  pinMode(LDR1, INPUT);
  pinMode(LDR2, INPUT);
  pinMode(LDR3, INPUT);
  pinMode(LDR4, INPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ ESP32 ready");
}

void loop() {

  // ====================================================
  // 🔆 READ & NORMALIZE LDRs (FINAL FIX)
  // ====================================================
  int l1 = analogRead(LDR1);
  int l2 = analogRead(LDR2);
  int l3 = analogRead(LDR3);
  int l4 = analogRead(LDR4);

  int leftAvg   = (l1 + l3) / 2;
  int rightAvg  = (l2 + l4) / 2;
  int topAvg    = (l1 + l2) / 2;
  int bottomAvg = (l3 + l4) / 2;

  int diffLR = leftAvg - rightAvg;
  int diffTB = topAvg - bottomAvg;

  int rawDiff = abs(diffLR) + abs(diffTB);

  // ---- Normalize to 0–100 % ----
  float ldrPercent = (rawDiff / LDR_MAX_DIFF) * 100.0;
  ldrPercent = constrain(ldrPercent, 0, 100);

  int ldrDiff = (int)ldrPercent;

  // ====================================================
  // ⚡ READ POWER (UNCHANGED)
  // ====================================================
  float voltage = ina219.getBusVoltage_V()
                + ina219.getShuntVoltage_mV() / 1000.0;

  float current = ina219.getCurrent_mA() / 1000.0;
  float power   = voltage * current;

  // ---- DEBUG ----
  Serial.printf(
    "RAW=%d | LDR=%d%% | V=%.3fV | I=%.6fA | P=%.6fW\n",
    rawDiff, ldrDiff, voltage, current, power
  );

  // ====================================================
  // 📡 SEND SENSOR DATA
  // ====================================================
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(sensorUrl);
    http.addHeader("Content-Type", "application/json");

    String payload = "{";
    payload += "\"ldr_diff\":" + String(ldrDiff) + ",";
    payload += "\"voltage\":" + String(voltage, 4) + ",";
    payload += "\"current\":" + String(current, 6) + ",";
    payload += "\"power\":"   + String(power,   6);
    payload += "}";

    http.POST(payload);
    http.end();
  }

  // ====================================================
  // 🤖 FETCH AI DECISION
  // ====================================================
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(decisionUrl);

    if (http.GET() == 200) {
      String body = http.getString();
      int i = body.indexOf("\"decision\":\"");
      if (i > 0) {
        String cmd = body.substring(i + 12, body.indexOf("\"", i + 12));
        ArduinoSerial.println(cmd);
        Serial.println("➡ AI → Arduino: " + cmd);
      }
    }
    http.end();
  }

  delay(2000);
}

