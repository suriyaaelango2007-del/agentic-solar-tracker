#include <Servo.h>

/* ================= LDR PINS ================= */
#define LDR1 A0
#define LDR2 A1
#define LDR3 A2
#define LDR4 A3

/* ================= SERVO ================= */
Servo tiltServo;
#define SERVO_PIN 9
int servoAngle = 90;
const int SERVO_MIN = 30;
const int SERVO_MAX = 150;

/* ================= STEPPER ================= */
int stepPins[4] = {6, 5, 4, 3};

int stepSeq[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};

int stepIndex = 0;
int stepDelay = 8;

/* ================= AI ================= */
String aiCommand = "HOLD_POSITION";

void setup() {
  Serial.begin(9600);   // UART to ESP32

  tiltServo.attach(SERVO_PIN);
  tiltServo.write(servoAngle);

  for (int i = 0; i < 4; i++) pinMode(stepPins[i], OUTPUT);

  Serial.println("ARDUINO_READY");
}

void loop() {
  /* ---------- READ LDR ---------- */
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

  int ldrDiff = max(abs(diffLR) + abs(diffTB));

  /* ---------- SEND LDR JSON TO ESP32 ---------- */
  Serial.print("{\"ldr_diff\":");
  Serial.print(ldrDiff);
  Serial.println("}");

  /* ---------- RECEIVE AI COMMAND ---------- */
  if (Serial.available()) {
    aiCommand = Serial.readStringUntil('\n');
    aiCommand.trim();
  }

  /* ---------- EXECUTE AI COMMAND ---------- */
  if (aiCommand == "ROTATE_TOWARDS_LIGHT") {
    if (diffLR > 20) rotateCW();
    else if (diffLR < -20) rotateCCW();

    if (diffTB > 20 && servoAngle < SERVO_MAX) servoAngle++;
    else if (diffTB < -20 && servoAngle > SERVO_MIN) servoAngle--;

    tiltServo.write(servoAngle);
  }
  else if (aiCommand == "PARK_PANEL") {
    parkPanel();
  }
  // HOLD_POSITION → do nothing

  delay(200);
}

/* ================= MOTOR FUNCTIONS ================= */

void rotateCW() {
  stepIndex = (stepIndex + 1) % 8;
  applyStep();
}

void rotateCCW() {
  stepIndex = (stepIndex - 1 + 8) % 8;
  applyStep();
}

void applyStep() {
  for (int i = 0; i < 4; i++)
    digitalWrite(stepPins[i], stepSeq[stepIndex][i]);
  delay(stepDelay);
}

void parkPanel() {
  servoAngle = 90;
  tiltServo.write(servoAngle);
  for (int i = 0; i < 60; i++) rotateCCW();
}
