#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_INA219.h>

// ================= WIFI =================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

const char* sensorUrl   = "http://10.26.153.48:5000/api/sensor";
const char* decisionUrl = "http://10.26.153.48:5000/api/state";

// ================= INA219 =================
Adafruit_INA219 ina219;

// ================= SERVOS =================
Servo azimuthServo;
Servo elevationServo;

#define AZ_PIN 18
#define EL_PIN 19

int azimuthAngle = 90;
int elevationAngle = 45;

// ================= LDR =================
#define LDR1 32
#define LDR2 33
#define LDR3 34
#define LDR4 35

#define LDR_MAX_DIFF 3000.0
#define TRACK_THRESHOLD 10
#define STEP_SIZE 2

#define PARK_AZ 90
#define PARK_EL 0

String currentDecision = "HOLD_POSITION";

// ======================================================
// WIFI CONNECT
// ======================================================
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

// ======================================================
// READ LDR
// ======================================================
void readLDR(int &diffLR, int &diffTB, int &percentImbalance) {

  int l1 = analogRead(LDR1);
  int l2 = analogRead(LDR2);
  int l3 = analogRead(LDR3);
  int l4 = analogRead(LDR4);

  int leftAvg   = (l1 + l3) / 2;
  int rightAvg  = (l2 + l4) / 2;
  int topAvg    = (l1 + l2) / 2;
  int bottomAvg = (l3 + l4) / 2;

  diffLR = leftAvg - rightAvg;
  diffTB = topAvg - bottomAvg;

  int rawDiff = max(abs(diffLR), abs(diffTB));

  float percent = (rawDiff / LDR_MAX_DIFF) * 100.0;
  percent = constrain(percent, 0, 100);

  percentImbalance = (int)percent;
}

// ======================================================
// SEND SENSOR DATA
// ======================================================
void sendSensor(int ldrPercent, float voltage, float current, float power) {

  HTTPClient http;
  http.begin(sensorUrl);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"ldr_diff\":" + String(ldrPercent) + ",";
  payload += "\"voltage\":" + String(voltage, 4) + ",";
  payload += "\"current\":" + String(current, 6) + ",";
  payload += "\"power\":" + String(power, 6);
  payload += "}";

  int code = http.POST(payload);

  Serial.print("POST Response: ");
  Serial.println(code);

  http.end();
}

// ======================================================
// FETCH AI DECISION
// ======================================================
void fetchDecision() {

  HTTPClient http;
  http.begin(decisionUrl);

  if (http.GET() == 200) {
    String body = http.getString();

    DynamicJsonDocument doc(1024);
    if (!deserializeJson(doc, body)) {
      currentDecision = doc["decision"] | "HOLD_POSITION";
    }
  }

  http.end();
}

// ======================================================
// AUTO TRACKING (FINAL CALIBRATED)
// ======================================================
void autoTrack(int diffLR, int diffTB) {

  // ---- Horizontal (Azimuth) ----
  if (abs(diffLR) > TRACK_THRESHOLD) {
    if (diffLR > 0)
      azimuthAngle -= STEP_SIZE;   // LEFT stronger
    else
      azimuthAngle += STEP_SIZE;   // RIGHT stronger
  }

  // ---- Vertical (Elevation) ----
  if (abs(diffTB) > TRACK_THRESHOLD) {
    if (diffTB > 0)
      elevationAngle += STEP_SIZE;   // TOP stronger
    else
      elevationAngle -= STEP_SIZE;   // BOTTOM stronger
  }

  azimuthAngle = constrain(azimuthAngle, 0, 180);
  elevationAngle = constrain(elevationAngle, 0, 90);

  azimuthServo.write(azimuthAngle);
  elevationServo.write(elevationAngle);
}

// ======================================================
// PARK MODE
// ======================================================
void parkPanel() {

  if (azimuthAngle != PARK_AZ) {
    if (azimuthAngle < PARK_AZ)
      azimuthAngle += STEP_SIZE;
    else
      azimuthAngle -= STEP_SIZE;
  }

  if (elevationAngle != PARK_EL) {
    if (elevationAngle < PARK_EL)
      elevationAngle += STEP_SIZE;
    else
      elevationAngle -= STEP_SIZE;
  }

  azimuthServo.write(azimuthAngle);
  elevationServo.write(elevationAngle);
}

// ======================================================
// SETUP
// ======================================================
void setup() {

  Serial.begin(115200);
  Wire.begin(21, 22);

  if (!ina219.begin()) {
    Serial.println("INA219 not found!");
    while (1);
  }

  ina219.setCalibration_32V_2A();

  azimuthServo.attach(AZ_PIN, 500, 2400);
  elevationServo.attach(EL_PIN, 500, 2400);

  azimuthServo.write(azimuthAngle);
  elevationServo.write(elevationAngle);

  pinMode(LDR1, INPUT);
  pinMode(LDR2, INPUT);
  pinMode(LDR3, INPUT);
  pinMode(LDR4, INPUT);

  analogSetPinAttenuation(LDR1, ADC_11db);
  analogSetPinAttenuation(LDR2, ADC_11db);
  analogSetPinAttenuation(LDR3, ADC_11db);
  analogSetPinAttenuation(LDR4, ADC_11db);

  connectWiFi();
}

// ======================================================
// MAIN LOOP
// ======================================================
void loop() {

  if (WiFi.status() != WL_CONNECTED)
    connectWiFi();

  int diffLR = 0;
  int diffTB = 0;
  int imbalancePercent = 0;

  readLDR(diffLR, diffTB, imbalancePercent);

  float voltage = ina219.getBusVoltage_V()
                  + ina219.getShuntVoltage_mV() / 1000.0;

  float current = ina219.getCurrent_mA() / 1000.0;
  float power   = voltage * current;

  sendSensor(imbalancePercent, voltage, current, power);

  fetchDecision();

  if (currentDecision == "ROTATE_TOWARDS_LIGHT")
    autoTrack(diffLR, diffTB);

  else if (currentDecision == "PARK_PANEL")
    parkPanel();

  Serial.printf("Decision: %s | LDR%%=%d | diffLR=%d | diffTB=%d | AZ=%d | EL=%d\n",
                currentDecision.c_str(),
                imbalancePercent,
                diffLR,
                diffTB,
                azimuthAngle,
                elevationAngle);

  delay(500);
}