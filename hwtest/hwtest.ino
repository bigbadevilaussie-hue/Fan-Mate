// hwtest.ino — simple hardware test
// Fan at 4 steps, LED, buzzer, NTC + Hall sensor
// Press RST to run again.

#include <Arduino.h>

// ── Pins ──────────────────────────────────────────────
#define FAN_PWM_PIN   7
#define TACH_PIN      3
#define BUZZER_PIN    10
#define LED_PIN       8
#define NTC_PIN       0
#define HALL_PIN      1          // A3144 on GPIO 1 (PHONE_SENSE)

// ── PWM ───────────────────────────────────────────────
#define PWM_FREQ      25000
#define PWM_RES       8
#define PWM_MIN       40

// ── Fan test steps ────────────────────────────────────
const int STEPS[] = {25, 50, 75, 100};
const int N_STEPS = sizeof(STEPS) / sizeof(STEPS[0]);
const unsigned long STEP_MS = 10000;

// ── NTC ───────────────────────────────────────────────
#define NTC_SERIES_R  10000.0
#define NTC_NOMINAL   10000.0
#define NTC_BETA      3950.0
#define NTC_T0        298.15

// ── Tach ──────────────────────────────────────────────
static volatile unsigned long tachPulses = 0;
static unsigned long lastTachRead = 0;
static int currentRPM = 0;

void IRAM_ATTR onTach() {
  tachPulses++;
}

// ── Helpers ───────────────────────────────────────────
void updateTach() {
  unsigned long now = millis();
  if (now - lastTachRead >= 1000) {
    noInterrupts();
    unsigned long pulses = tachPulses;
    tachPulses = 0;
    interrupts();

    lastTachRead = now;
    currentRPM = (pulses * 60) / 2;
  }
}

void setFan(int pct) {
  int pwm = 0;
  if (pct > 0) {
    pwm = map(pct, 1, 100, PWM_MIN, 255);

    if (currentRPM < 200) {
      ledcWrite(0, 200);
      delay(400);
    }
  }
  ledcWrite(0, pwm);
}

float readNTC() {
  long sum = 0;
  for (int i = 0; i < 4; i++) {
    sum += analogRead(NTC_PIN);
    delayMicroseconds(50);
  }
  int raw = sum / 4;

  if (raw <= 0 || raw >= 4095) return -99.0f;

  float v_out = raw * (3.3f / 4095.0f);
  float r_ntc = NTC_SERIES_R * (v_out / (3.3f - v_out));

  float steinhart = log(r_ntc / NTC_NOMINAL) / NTC_BETA;
  steinhart += 1.0 / NTC_T0;
  float temp_k = 1.0 / steinhart;
  return temp_k - 273.15;
}

// ── Setup ─────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("========================================");
  Serial.println("  HARDWARE TEST");
  Serial.println("  Fan · LED · Buzzer · NTC · Hall");
  Serial.println("  Press RST to run again");
  Serial.println("========================================");
  Serial.println();

  // LED off (active-LOW)
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // Fan PWM
  ledcSetup(0, PWM_FREQ, PWM_RES);
  ledcAttachPin(FAN_PWM_PIN, 0);
  ledcWrite(0, 0);

  // Buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // Tach
  pinMode(TACH_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(TACH_PIN), onTach, FALLING);

  // NTC
  analogReadResolution(12);
  pinMode(NTC_PIN, INPUT);

  // Hall sensor (A3144) - active LOW when magnet present
  pinMode(HALL_PIN, INPUT_PULLUP);

  Serial.println("Starting in 2s...");
  delay(2000);
}

// ── Main loop ─────────────────────────────────────────
void loop() {
  // 1. Fan sweep
  for (int i = 0; i < N_STEPS; i++) {
    int pct = STEPS[i];
    setFan(pct);

    unsigned long start = millis();
    int lastReport = -1;

    while (millis() - start < STEP_MS) {
      updateTach();

      int elapsed = (millis() - start) / 1000;

      if (elapsed > 0 && elapsed > lastReport) {
        lastReport = elapsed;

        int raw = analogRead(NTC_PIN);
        float ntc_c = readNTC();

        // Hall sensor: LOW = magnet present = ON
        bool hallOn = (digitalRead(HALL_PIN) == LOW);

        Serial.printf("Fan %3d%%  RPM %4d  |  NTC raw %4d  %.1f C  |  Hall: %s\n",
                      pct, currentRPM, raw, ntc_c,
                      hallOn ? "ON " : "OFF");
      }
      delay(50);
    }
  }
  setFan(0);

  // 2. Buzzer
  Serial.println();
  Serial.println("--- buzzer ---");
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 2000, 150);
    delay(200);
    noTone(BUZZER_PIN);
    delay(100);
  }
  Serial.println("--- done ---");

  // 3. LED flash
  Serial.println("--- LED flash ---");
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(150);
    digitalWrite(LED_PIN, HIGH);
    delay(150);
  }
  Serial.println("--- done ---");

  Serial.println();
  Serial.println("=== Press RST to run again ===");
  Serial.println();

  while (1) {
    delay(1000);
  }
}